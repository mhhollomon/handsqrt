#!/usr/bin/env python

import argparse
from collections import namedtuple, deque

Iteration = namedtuple('Iteration', ( 'group', 'digit', 'guess', 'start', 'epsilon', 'partial' ))

DEFAULT_EXTRA_LOOPS = 2

GROUPINGS = (
        'units',
        'thousand',
        'million',
        'billion',
        'trillion',
        'quadrillion',
        'quintillion',
        'sextillion',
        'septillion',
        'octillion',
        )

debug_active = False

def debug(*msg) :
    if debug_active :
        print(*msg)
parser = argparse.ArgumentParser()

parser.add_argument('target', help="Number to estimate the square root of")
parser.add_argument('-l','--loops', type=int, default=DEFAULT_EXTRA_LOOPS, 
        help="Number of loops to continue after consuming all data")
parser.add_argument('-x','--html',
        help="Name of file for html output")
parser.add_argument('-d', '--debug', action='store_true',
        help="Turn on debugging output")

args = parser.parse_args()

# debug
debug_active = args.debug

# number of loops to do over and above consuming all groups
extra_loops = args.loops

html = False
html_file = None
if args.html :
    html = True
    html_file = args.html

# Note that we can't use regex for this because repeated subgroups ( e.g. (\d{2})* )
# only make the last match available. SO, we need to do this a different way.
#
# Note also, that python 3 use bigint for integer by default. Which is exactly whay we want.
# but if we divide - remember to use // rather than /

whole, fract = args.target.split('.')

debug(f"whole = '{whole}'")
debug(f"fract = '{fract}'")

groups = []

# break the whole part into groups of 2 digits. Figuratively start from the
# ones position - which means the "first" group may only have one digit in it.
# e.g. 123 => (1)(23)

# I chose to use an iterator rather than continually chopping characters off
# the string, because strings in python are immutable - which means you would
# be continuously copying things when doing something like:
#   target = target[2:]


curr_index = 0
if len(whole) % 2 == 1 :
    groups.append(int(whole[curr_index:curr_index+1]))
    curr_index += 1
while curr_index < len(whole) :
    groups.append(int(whole[curr_index:curr_index+2]))
    curr_index += 2

# WE will ge a digit in our answer for every group. So the the number
# of groups obtained from the whole number is how many answer digits will
# be to the left of the decimal.
answer_decimal_index = len(groups)

# Now, same for fracts, but starting from the dot means starting from the front
# Its the LAST group that might be fishy. .123 => (12)(30)

curr_index = 0
while curr_index < len(fract) :
    groups.append(int(fract[curr_index:curr_index+2]))
    curr_index += 2

if groups[-1] < 10 :
    # pretend there was an extra zero on the end
    groups[-1] *= int(10)

debug(repr(groups))

iterations = deque()

#------------------------------------
# Step 1.
# estimate the square root of the beginning
# group. Since it was made from at most two digits,
# it will be between 1 and 99 - its sqrt will be
# in the range 1 to 9 - so just try it.
#
curr_index = 0
curr_group = groups[curr_index]
guess = 0
for i in range(1, 10) :
    if i*i <= curr_group :
        guess = i
    else :
        break

answer = guess
partial = curr_group - (guess * guess)
curr_index += 1
answer_digits = 1

iterations.append(Iteration(curr_group, guess, guess, curr_group, guess*guess, partial))

debug("#---", repr(iterations[0]))

debug("answer = ", answer)
debug("partial = ", partial)

#----------------------------------
# Step 2 - N
# Take the answer and double.
# use that as the next divisor. Recalc the partial
#

while  True :
    if extra_loops < 0 :
        break
    elif curr_index < len(groups) :
        curr_group = groups[curr_index]
        curr_index += 1
    else :
        curr_group = 0
        extra_loops -= 1
    debug("-------------------")
    debug ("curr_group = ", curr_group)

    start_partial = (partial * 100) + curr_group
    debug("new partial =", start_partial)
    guess_kernel = (answer * 2) * 10
    debug ("guess_kernel =", guess_kernel)
    new_digit = 0
    for d in range(9,-1, -1) :
        if ((guess_kernel + d) * d) < start_partial :
            new_digit = d
            break
    guess = guess_kernel + new_digit
    debug("guess =", guess)
    epsilon = guess * new_digit
    partial = start_partial - epsilon
    answer = (answer * 10) + new_digit
    answer_digits += 1
    debug("new_digit = ", new_digit)
    debug("epsilon = ", epsilon)
    debug("partial = ", partial)
    debug("answer = ", answer)
    iterations.append(Iteration(curr_group, new_digit, guess, start_partial, epsilon, partial))

# Note that our answer is an int and needs to be scaled.
# But we might not get a precise answer if we try to use floats
# So, do things as strings.

answer_string = str(answer)

answer_string = answer_string[:answer_decimal_index] + '.' + answer_string[answer_decimal_index:]

import decimal
from decimal import Decimal

estimate = Decimal(answer_string)
original = Decimal(args.target)

square = estimate * estimate
epsilon = abs(square - original)

ratio = epsilon/original

ratio_tuple = ratio.as_tuple()

grouping, parts_size = divmod(ratio.adjusted(), 3)
grouping = abs(grouping)

debug(f"g = {grouping} ps = {parts_size}")
#parts_size += 1

grouping = GROUPINGS[grouping]

parts = Decimal((0, ratio_tuple.digits[:parts_size+1], 0))


print(f"Final estimate = {answer_string}\nThe estimate**2 = {square} - off by {epsilon}")
print(f"ratio = {ratio} ( {parts} parts per {grouping} )")

#-------------
# html output
if html :
    # for now just ascii
    print("#----------------------------")
    # print out the estimate
    digits = list(answer_string)
    spaced_answer = ' '.join(digits)
    spaced_answer = spaced_answer.replace(' .', '.')
    if (groups[0] >= 10)  :
        spaced_answer =  ' ' + spaced_answer
    pre = ' '*5

    print(f"{pre} {spaced_answer}")

    target = str(args.target)
    underbars = '_' * len(target)
    print (f"{pre} {underbars}")

    # print out the target
    print(f"{pre}/{args.target}")

    curr_iter = iterations.popleft()
    epsilon = curr_iter.epsilon

    pre = ' '*6
    if curr_iter.group < 10 :
        epsilon = str(epsilon)
    else :
        epsilon = f"{epsilon:2d}"
    print(f"{pre}{epsilon}")
    underbar = '-'*len(str(epsilon))
    output = f"{pre}{underbar}"
    print(output)
    right_side = len(output)
    bar_size = len(underbar)

    while iterations :
        curr_iter = iterations.popleft()

        # new partial with the new group appended
        start_partial = str(curr_iter.start)

        divisor = f"{curr_iter.guess}*{curr_iter.digit} < "

        # this is where the divisor must stop
        left_side = right_side - bar_size

        pre = ' ' *(left_side - len(divisor))

        bar_size = len(start_partial)
        output = f"{pre}{divisor}{start_partial}"
        print(output)
        right_side = len(output)

        print(f"{curr_iter.epsilon:>{right_side}}")
        underbar = '-' * bar_size
        print(f"{underbar:>{right_side}}")


    # partial from last iteration
    print(f"{curr_iter.partial:>{right_side}}")
