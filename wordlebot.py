import yaml
import re
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

FIRST="NEATO"

currChars = FIRST

DEFAULT_HISTO = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0, "f": 0, "g": 0, "h": 0, "i": 0, "j": 0, "k": 0, "l": 0, "m": 0, "n": 0, "o": 0, "p": 0, "q": 0, "r": 0, "s": 0, "t": 0, "u": 0, "v": 0, "w": 0, "x": 0, "y": 0, "z": 0 }

def scoreWords( filteredWords ):
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
            score += fiveHistos[idx][letter] * freqs[letter]  # joint probability
            idx += 1
        scoredWords[filteredWord] = score
    rankedWords = [ v[0] for v in sorted(scoredWords.items(), key=lambda item: item[1]) ]
    rankedWords.reverse()
    print(rankedWords)

with open( f"{SCRIPT_DIR}/letterFreqs.yml", "r" ) as f:

    freqs = yaml.safe_load( f )

# First, get a queue of letters ordered from most to least common.
letterQueue = list( freqs.keys() ) # get letters in backwards order
letterQueue.reverse()  # so we pop them out from most to least common
lettersRemaining = letterQueue.copy()  # so we pop them out from most to least common
lettersRemaining.sort()  # so we pop them out from most to least common

# Second, load up all the valid words.
wordleState = "";
with open( f"{SCRIPT_DIR}/validWords.txt", "r" ) as f:
    validWords = f.read()

# Remove newlines
for idx in range(len(validWords)):
    validWords[idx] = validWords[idx].strip()

# TODO this is a game mechanism to be impl'd later
guesses = { 0: [""], 1: [""], 2: [""], 3: [""], 4: [""], 5: [""] }
lockedGreens = "     "
for turn in range( len(guesses) ):
    # UPPER-case letters = green
    # lower-case letters = yellow
    # spaces             = wrong

    scoreWords(validWords)
    # Step 1: Make your guess
    while True:
        print( f"Input your guess #{turn + 1}." )
        guess = input().lower()
        if len(guess) != 5:
            print( "Your guess isn't 5 letters long. Guess again." )
            continue
        elif guess not in validWords:
            print( "Your guess is not a valid word. Guess again." )
            continue
        else:
            for letter in guess:
                if letter not in lettersRemaining:
                    print( f"Letter {letter} is not in the list of remaining letters. Guess again." )
                    continue
        break

    # Step 2: Tell wordlebot the outcome
    while True:
        print( "What was the outcome? A-Z = green letter, a-z = yellow, <space> = gray" )
        outcome = input()
        if len(outcome) != 5:
            print( "Your outcome needs to be 5 characters, even if whitespaces." )
            continue
        else:
            tryAgain = False
            for idx in range(5):
                if outcome[idx] != ' ' and outcome[idx].lower() != guess[idx].lower():
                    print( f"The letter {outcome[idx]} doesn't match your guess in spot {idx}. Try again." )
                    tryAgain = True
                    break
            if tryAgain:
                continue
        regex = ""
        greens = set()
        yellows = set()

        # Put letters in green/yellow bins or 
        idx = 0
        for outcomeLetter in outcome:
            # outcome's letter is GREEN
            if outcomeLetter.isupper():
                regex += outcomeLetter.lower()
                greens.add(outcomeLetter)
                listedMasterRegex = list(lockedGreens)
                listedMasterRegex[idx] = outcomeLetter.lower()
                lockedGreens = "".join( listedMasterRegex )
            # outcome's outcomeLetter is YELLOW or GRAY
            else:
                if outcomeLetter.islower():
                    yellows.add(outcomeLetter)
                    regex += '#'   # will be filled in later
                elif outcomeLetter == ' ':
                    grayLetter = guess[idx]
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
                print( f"seeing if letter {usedLetter} is in {usedLettersInThisSpot}" )
                if usedLetter in validLetters:
                    print( f"removing letter {usedLetter} from spot {idx}" )
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
        filteredWords = r.findall( validWords )

        # Do a second pass with the yellows. Get rid of validWords missing a yellow.
        # First, mask out the greens.
        wordsToRemove = []
        for filteredWord in filteredWords:
            origFilteredWord = filteredWord
            idx = 0
            # Mask out greens.
            listedFilteredWord = list(filteredWord)
            for greenIdx in range(len(lockedGreens)):
                if lockedGreens[idx] != ' ':
                    listedFilteredWord[idx] = '-'
            filteredWord = "".join( listedFilteredWord )
            # Filter for masked validWords that have all the yellows.
            for yellow in yellows:
                if yellow not in filteredWord:
                    wordsToRemove.append( origFilteredWord )
                    break
            idx += 1

        # Then remove validWords that don't have ALL the yellows in them.
        for wordToRemove in wordsToRemove:
            filteredWords.remove( wordToRemove )

        validWords = filteredWords

    if ' ' not in lockedGreens:
        print( f"Congrats! You did it in {turn + 1} turns." )
        exit(0)
print( "Youuuu ahhh aaa FAYYYYLURRRRRR" )
