import yaml
import re
import os
import sys
import random

#if len(sys.argv) != 2:
    #print("Expected usage:\n\twb <word-of-the-day>")

answer = sys.argv[1]

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[33m"
MAGENTA = "\033[95m"
GRAY = "\033[90m"
RESET = "\033[0m"
WHITE = RESET

FIRST="NEATO"

currChars = FIRST

DEFAULT_HISTO = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0, "f": 0, "g": 0, "h": 0, "i": 0, "j": 0, "k": 0, "l": 0, "m": 0, "n": 0, "o": 0, "p": 0, "q": 0, "r": 0, "s": 0, "t": 0, "u": 0, "v": 0, "w": 0, "x": 0, "y": 0, "z": 0 }

def guessWord( filteredWords ):
    # Histogram the letter occurrences in each one.
    fiveHistos = 5 * [ DEFAULT_HISTO.copy() ] 
    for idx in range(5):
        # Histogram the letters of all filtered validWords in each spot.
        for fw in filteredWords:
            for letter in fw:
                fiveHistos[idx][letter] += 1
        # Divide each count by total to get its probability.
        for letterPos in range(5):
            fiveHistos[idx][letter] /= len(filteredWords)
        idx += 1

    # Score the remaining validWords by their letter frequencies.
    scoredWords = {}
    for filteredWord in filteredWords:
        # don't multi-count any letter = variety scores higher to rule out more possibilities
        #for letter in set(filteredWord.lower()):   
            #score += freqs[letter]
        score = 0
        idx = 0
        for letter in set(filteredWord.lower()):
            # score += fiveHistos[idx][letter] 
            score += fiveHistos[idx][letter] # what if we don't base it on a corpus, but our own...?
            # score += fiveHistos[idx][letter] * freqs[letter]  # joint probability
            idx += 1
        scoredWords[filteredWord] = score
    rankedWords = [ v[0] for v in sorted(scoredWords.items(), key=lambda item: item[1]) ]
    rankedWords.reverse()
    return rankedWords[0].lower()

def prompt( guess, turnNum ):
    order = [ "first", "second", "third", "fourth", "fifth", "final" ]
    response = f"{MAGENTA}{guess.upper()}{WHITE} is my {order[turnNum]} guess.{RESET}"
    print( response )

lettersRemaining = [ "a" , "b" , "c" , "d" , "e" , "f" , "g" , "h" , "i" , "j" , "k" , "l" , "m" , "n" , "o" , "p" , "q" , "r" , "s" , "t" , "u" , "v" , "w" , "x" , "y" , "z" ]

# Second, load up all the valid words.
wordleState = "";
with open( f"{SCRIPT_DIR}/validWords.txt", "r" ) as f:
    validWords = f.read()

validWords = validWords.split("\n")
# Remove newlines
for idx in range(len(validWords)):
    validWords[idx] = validWords[idx].strip()

# INTO
print( f"{WHITE}Hi, I'm Wordle Bot!\nI want to guess today's Wordle.{RESET}" )
print( f"{WHITE}Here's how you talk to me:{RESET}" )
print( f"{GREEN}  * GREEN  letter = upper-case{RESET}" )
print( f"{YELLOW}  * YELLOW letter = lower-case{RESET}" )
print( f"{WHITE}  * GRAY   letter = <space>{RESET}" )

guesses = { 0: [""], 1: [""], 2: [""], 3: [""], 4: [""], 5: [""] }
lockedGreens = "     "
for turn in range( len(guesses) ):
    # UPPER-case letters = green
    # lower-case letters = yellow
    # spaces             = wrong

    # Step 1: Machine makes a guess.
    guess = guessWord(validWords)
    prompt(guess, turn)

    # Step 2: Tell wordlebot the outcome.
    while True:
        outcome = input()
        if len(outcome) != 5:
            print( f"{RED}Your outcome needs to be 5 characters, even if whitespaces.{RESET}" )
            continue
        else:
            tryAgain = False
            for idx in range(5):
                if outcome[idx] != ' ' and outcome[idx].lower() != guess[idx].lower():
                    print( f"{RED}The letter {outcome[idx]} doesn't match your guess in spot {idx}. Try again.{RESET}" )
                    tryAgain = True
                    break
            if tryAgain:
                continue
        regex = ""
        greens = set()
        yellows = set()

        # Put letters in green/yellow/gray bins.
        idx = 0
        for outcomeLetter in outcome:
            # outcomeLetter is GREEN
            if outcomeLetter.isupper():
                regex += outcomeLetter.lower()
                greens.add(outcomeLetter)
                listedMasterRegex = list(lockedGreens)
                listedMasterRegex[idx] = outcomeLetter.lower()
                lockedGreens = "".join( listedMasterRegex )
            # outcomeLetter is YELLOW or GRAY
            else:
                if outcomeLetter.islower():
                    yellows.add(outcomeLetter)
                    regex += '#'   # will be filled in later
                elif outcomeLetter == ' ':
                    grayLetter = guess[idx].lower()
                    if grayLetter in lettersRemaining:
                        lettersRemaining.remove(grayLetter.lower() )
                    regex += ' '
            idx += 1

        # Build the regex expression to filter for remaining validWords.
        idx = 0
        finalregex = r""
        for reChar in regex:
            # Skip greens.
            if reChar not in [ '#', ' ' ]:
                finalregex += reChar
                idx += 1
                continue
            # Don't let dumb guesses cause the filter to yield false positives.
            elif lockedGreens[idx] != ' ':
                finalregex += lockedGreens[idx]
                idx += 1
                continue
            validLetters = lettersRemaining.copy()
            # Rule out letters already used in this spot.
            usedLettersInThisSpot = [ prevGuess[idx] for prevGuess in guesses.values() if len(prevGuess) > idx ]
            for usedLetter in usedLettersInThisSpot:
                if usedLetter in validLetters:
                    validLetters.remove( usedLetter )
            # Since this letter isn't green, invalidate it for the filtered possible answers.
            if guess[idx] in validLetters:
                validLetters.remove( guess[idx] )
            finalregex += "[" + "".join(validLetters) + "]"
            idx += 1

        # Keep track of your guesses to prevent double-dipping any letters in the same spot.
        guesses[turn] = guess

        # Filter for validWords matching our regex.
        r = re.compile( finalregex )
        unfilteredWords =  " ".join( validWords )
        filteredWords = r.findall(unfilteredWords)

        # Do a second pass with the yellows. Get rid of validWords missing a yellow.
        # First, mask out the greens.
        indicesToRemove = []
        wordIdx = 0
        # (Performance boost: Popping by index is WAY FASTER than search-based word removal.
        for wordIdx in range( len( filteredWords ) ):
            origFilteredWord = filteredWords[wordIdx]
            letterIdx = 0
            # Mask out greens.
            listedFilteredWord = list(origFilteredWord)
            for greenIdx in range(len(lockedGreens)):
                if lockedGreens[letterIdx] != ' ':
                    listedFilteredWord[letterIdx] = '-'
            # Filter for masked validWords that have all the yellows.
            for yellow in yellows:
                if yellow not in origFilteredWord:
                    indicesToRemove.append( wordIdx )
                    break

        # Then remove validWords that don't have ALL the yellows in them.
        indicesToRemove.reverse()   #  so we don't change positions of things we're erasing
        for idx in indicesToRemove:
            filteredWords.pop( idx )

        validWords = filteredWords
        break

    if ' ' not in lockedGreens:
        print( f"{GREEN}I did it in {turn + 1} turns. Can you beat that?{RESET}" )
        exit(0)
print( "{RED}Youuuuu have createddddd a FAIILLLYYORRRRRR{RESET}" )
