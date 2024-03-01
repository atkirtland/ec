import datetime
import os
import random

import binutil  # required to import from dreamcoder modules

from dreamcoder.ec import commandlineArguments, ecIterator
from dreamcoder.grammar import Grammar
from dreamcoder.program import *
from dreamcoder.task import Task
from dreamcoder.type import arrow, tint, tpair, tbool, tlist, t0
from dreamcoder.utilities import numberOfCPUs

# Primitives
# def _zero(): return 0
# def _one(): return 1
def _incr(x): return x + 1
def _decr(x): return x - 1
def _modulo(x): return lambda n: x%n
def _eq(x): return lambda y: x==y
def _not(x): return not x
# def _if(x,y,z): return lambda x,y,z: y if x else z
def _if(c): return lambda t: lambda f: t if c else f
# def _concat(x,y): return lambda x,y: (x,y)
# def _left_separate(x,y): return lambda x,y: x
# def _right_separate(x,y): return lambda x,y: y
# def _empty(): return []
# def _append(l,a): return lambda l,a: l + a OLD

# def _index(l, i): return lambda l,i: l[i]
def _cons(x): return lambda y: [x] + y
# def _append(x): return lambda y: x + y
def _index(j): return lambda l: l[j]
def _add(x): return lambda y: x+y
def _mult(x): return lambda y: x*y

# def transitionN(d):
#     x = random.choice(range(d))
#     y = random.choice(range(d))
#     a = random.choice(range(4))
#     # up, down, left, right
#     if a == 0:
#         ox = x
#         oy = (y+1) % d
#     elif a == 1:
#         ox = x
#         oy = (y-1) % d
#     elif a == 2:
#         ox = (x-1) % d
#         oy = y
#     elif a == 3:
#         ox = (x+1) % d
#         oy = y
#     return {"i": (x,y,a), "o": (ox,oy)}

def transitionN(d):
    x = random.choice(range(d))
    y = random.choice(range(d))
    a = random.choice(range(4))
    if a == 0:
        ox = x
        oy = (y if y==d-1 else y+1)
    elif a == 1:
        ox = x
        oy = (y if y==0 else y-1)
    elif a == 2:
        ox = (x if x==0 else x-1)
        oy = y
    elif a == 3:
        ox = (x if x==d-1 else x+1)
        oy = y
    # return (ox,oy)
    return {"i": (x,y,a), "o": (ox,oy)}

def transitionNR(d):
    x = random.choice(range(d))
    y = random.choice(range(d))
    a = random.choice(range(4))
    if a == 0:
        ox = x
        oy = (y if y==d-1 else y+1)
    elif a == 1:
        ox = x
        oy = (y if y==0 else y-1)
    elif a == 2:
        ox = (x if x==0 else x-1)
        oy = y
    elif a == 3:
        ox = (x if x==d-1 else x+1)
        oy = y

    rx = 1
    ry = 1
    if ox == rx and oy == ry:
        r = 1
    else:
        r = 0
    return {"i": (x,y,a), "o": (ox,oy,r)}

# s1 = "(if (eq? (index 1 $0) (decr $1)) (index 1 $0) (incr (index 1 $0)))"
# s2 = "(if (eq? (index 1 $0) 0) (index 1 $0) (decr (index 1 $0)))"
# s3 = "(if (eq? (index 0 $0) 0) (index 0 $0) (decr (index 0 $0)))"
# s4 = "(if (eq? (index 0 $0) (decr $1)) (index 0 $0) (incr (index 0 $0)))"
# tests = f"""(lambda (lambda (
#     if (eq? (index 2 $0) 0) (cons (index 0 $0) (cons {s1} empty)) (
#         if (eq? (index 2 $0) 1) (cons (index 0 $0) (cons {s2} empty)) (
#             if (eq? (index 2 $0) 2) (cons {s3} (cons (index 1 $0) empty)) (
#                 cons {s4} (cons (index 1 $0) empty)
#             )
#         )
#     )
# )))"""

s1 = "(if (eq? (index 1 $0) (decr $1)) (index 1 $0) (incr (index 1 $0)))"
s2 = "(if (eq? (index 1 $0) 0) (index 1 $0) (decr (index 1 $0)))"
s3 = "(if (eq? (index 0 $0) 0) (index 0 $0) (decr (index 0 $0)))"
s4 = "(if (eq? (index 0 $0) (decr $1)) (index 0 $0) (incr (index 0 $0)))"
tests = f"""(lambda (lambda (lambda (
    if (eq? (index 2 $0) 0) (cons (index 0 $0) (cons {s1} empty)) (
        if (eq? (index 2 $0) 1) (cons (index 0 $0) (cons {s2} empty)) (
            if (eq? (index 2 $0) 2) (cons {s3} (cons (index 1 $0) empty)) (
                cons {s4} (cons (index 1 $0) empty)
            )
        )
    )
))))"""

# rx = 1
# ry = 1
# r = 1
# testr = f"""(lambda (if (eq? (index 0 $0) {rx}) (if (eq? (index 1 $0) {ry}) {r} 0) 0))"""
# should take in the new coordinates and append the reward to the end
# (append (lambda (tests d) $0)


def ID2(d):
    x = random.choice(range(d))
    y = random.choice(range(d))
    return {"i": (x,y), "o": (x,x+y)}

def simple_transition_test(d):
    x = random.choice(range(d))
    a = random.choice(range(2))
    # up, down, left, right
    if a == 0:
        ox = (x+1) % d
    else:
        ox = (x-1) % d
    return {"i": (x,a), "o": ox}

def simple_mod_test(d):
    x = random.choice(range(d))
    return {"i": (x,), "o": (x-1) % d}

def simple_add_test(d):
    x = random.choice(range(d))
    y = random.choice(range(d))
    return {"i": (x,y), "o": x+y}

def simple_modxa_test(d):
    x = random.choice(range(d))
    a = 0
    return {"i": (x,a), "o": (x-1) % d}

def simple_eq_test(d):
    x = random.choice(range(d))
    y = random.choice(range(d))
    return {"i": [x,y], "o": [x==y]}

def simple_if_test(d):
    c = random.choice([True,False])
    # w = random.choice(range(d))
    x = random.choice(range(d))
    y = random.choice(range(d))
    # z = random.choice(range(d))
    return {"i": (c,x,y), "o": x if c else y}

# simple_test = simple_transition_test
# simple_test = simple_transition_test
# simple_test = simple_mod_test
simple_test = transitionN

def get_tint_task(item):
    return Task(
        item["name"],
        arrow(tlist(tint), tlist(tint)),
        [((ex["i"],), ex["o"]) for ex in item["examples"]],
    )
def get_strans_task(item):
    return Task(
        item["name"],
        arrow(tint, tint, tint),
        [(ex["i"], ex["o"]) for ex in item["examples"]],
    )

def get_ii_task(item):
    return Task(
        item["name"],
        arrow(tint, tint),
        [(ex["i"], ex["o"]) for ex in item["examples"]],
    )


def get_tbool_task(item):
    return Task(
        item["name"],
        arrow(tlist(tint), tlist(tbool)),
        [((ex["i"],), ex["o"]) for ex in item["examples"]],
    )

def get_if_task(item):
    return Task(
        item["name"],
        arrow(tbool, tint, tint, tint),
        [(ex["i"], ex["o"]) for ex in item["examples"]],
    )

def get_if2_task(item):
    return Task(
        item["name"],
        arrow(tlist(tint), tlist(tint)),
        [((ex["i"],), ex["o"]) for ex in item["examples"]],
    )

def get_transition_task(item):
    return Task(
        item["name"],
        arrow(tint, tint, tint, tint, tint),
        [(ex["i"], ex["o"]) for ex in item["examples"]],
    )

# get_task = get_strans_task
get_task = get_tint_task

if __name__ == "__main__":

    # Options more or less copied from list.py

    args = commandlineArguments(
        enumerationTimeout=10, activation='tanh',
        iterations=10, recognitionTimeout=3600,
        a=3, maximumFrontier=10, topK=2, pseudoCounts=30.0,
        helmholtzRatio=0.5, structurePenalty=1.,
        CPUs=numberOfCPUs())

    timestamp = datetime.datetime.now().isoformat()
    outdir = 'experimentOutputs/demo/'
    os.makedirs(outdir, exist_ok=True)
    outprefix = outdir + timestamp
    args.update({"outputPrefix": outprefix})

    # Create list of primitives

    primitives = [
        Primitive("-1", tint, -1),
        Primitive("0", tint, 0),
        Primitive("1", tint, 1),
        Primitive("2", tint, 2),
        Primitive("3", tint, 3),
        Primitive("4", tint, 4),
        Primitive("5", tint, 5),
        Primitive("6", tint, 6),
        Primitive("7", tint, 7),
        Primitive("8", tint, 8),
        Primitive("9", tint, 9),
        # Primitive("true", tbool, True),
        # Primitive("not", arrow(tbool, tbool), _not),
        Primitive("incr", arrow(tint, tint), _incr),
        Primitive("decr", arrow(tint, tint), _decr),
        # Primitive("mod", arrow(tint, tint, tint), _modulo),
        Primitive("eq?", arrow(tint, tint, tbool), _eq),
        Primitive("if", arrow(tbool, t0, t0, t0), _if),
        # Primitive("+", arrow(tint, tint, tint), _add),
        # Primitive("*", arrow(tint, tint, tint), _mult),

        Primitive("empty", tlist(t0), []),
        Primitive("cons", arrow(t0, tlist(t0), tlist(t0)), _cons),
        Primitive("index", arrow(tint, tlist(t0), t0), _index),

        # Program.parse("(lambda (lambda (mod (incr (+ $0 $1)) 7)))"),
        # Program.parse("(lambda (lambda (if (eq? $1 0) (mod (incr $0) 4) (mod (decr $0) 4))))"),
        # Program.parse("(lambda (lambda (if (eq? $1 0) (mod (incr $0) 4) (+ (mod (decr $0) 4) 4))))"),
        # Program.parse("(lambda (lambda (lambda (if (eq? $2 0) (mod (incr $1) $0) (+ (mod (decr $1) $0) $0)))))"),

        # Program.parse("(lambda (lambda (mod (+ $1 $0) $0)))"),

        # Program.parse("(lambda (lambda (mod (+ (decr $1) $0) $0)))"),
        # Program.parse("(lambda (lambda (modj (+ (decr $0) $1) $1)))"),
        # Program.parse("")
        # Program.parse("(lambda (+ (index 0 $0) (index 1 $0)))"),
        # Program.parse("(lambda (cons (index 0 $0) (cons (+ (index 0 $0) (index 1 $0)) empty)))"),

        # Program.parse("(lambda (lambda (if (eq? (index 0 $0) 0) (cons (0 $0) (cons (0) empty)) (if (eq? (index 0 $0) 1) (cons (0 $0) (cons (0) empty)) (if (eq? (index 0 $0) 2) (cons (0) (cons (1 $0) empty)) (cons (0) (cons (1 $0) empty)))))))"),
        Program.parse(' '.join(tests.split())),
        # Program.parse(' '.join(testr.split())),
    ]



    # Create grammar

    grammar = Grammar.uniform(primitives)

    # def transition2(): return transitionN(2)
    # def transition3(): return transitionN(3)
    # def transition4(): return transitionN(4)
    def simple_test2(): return simple_test(2)
    def simple_test3(): return simple_test(3)
    def simple_test4(): return simple_test(4)
    def simple_test5(): return simple_test(5)
    def simple_test6(): return simple_test(6)
    def simple_test7(): return simple_test(7)
    def simple_test8(): return simple_test(8)
    def simple_test9(): return simple_test(9)
    def simple_test10(): return simple_test(10)
    def simple_test11(): return simple_test(11)
    # def simple_test10(): return simple_test(10)
    # def simple_test100(): return simple_test(100)
    # def simple_test2(): return simple_test(2)
    # def simple_test3(): return simple_test(3)
    # def simple_test4(): return simple_test(4)
    # Training data

    training_examples = [
        {"name": "simple_train2", "examples": [simple_test2() for _ in range(5000)]},
        {"name": "simple_train3", "examples": [simple_test3() for _ in range(5000)]},
        {"name": "simple_train4", "examples": [simple_test4() for _ in range(5000)]},
        {"name": "simple_train5", "examples": [simple_test5() for _ in range(5000)]},
        {"name": "simple_train6", "examples": [simple_test6() for _ in range(5000)]},
        {"name": "simple_train7", "examples": [simple_test7() for _ in range(5000)]},
        {"name": "simple_train8", "examples": [simple_test8() for _ in range(5000)]},
        {"name": "simple_train9", "examples": [simple_test9() for _ in range(5000)]},
        {"name": "simple_train10", "examples": [simple_test10() for _ in range(5000)]},
        {"name": "simple_train11", "examples": [simple_test11() for _ in range(5000)]},
        # {"name": "simple_test100", "examples": [simple_test100() for _ in range(5000)]},
        # {"name": "transition2", "examples": [transition2() for _ in range(5000)]},
        # {"name": "transition3", "examples": [transition3() for _ in range(5000)]},
        # {"name": "transition4", "examples": [transition4() for _ in range(5000)]},
    ]
    training = [get_task(item) for item in training_examples]

    # Testing data

    testing_examples = [
        # {"name": "simple_test4", "examples": [simple_test4() for _ in range(5000)]},
        # {"name": "transition3", "examples": [transition3() for _ in range(5000)]},
        # {"name": "transition5", "examples": [transition5() for _ in range(500)]},
        {"name": "simple_test2", "examples": [simple_test2() for _ in range(5000)]},
        {"name": "simple_test3", "examples": [simple_test3() for _ in range(5000)]},
        {"name": "simple_test4", "examples": [simple_test4() for _ in range(5000)]},
        {"name": "simple_test5", "examples": [simple_test5() for _ in range(5000)]},
        {"name": "simple_test6", "examples": [simple_test6() for _ in range(5000)]},
        {"name": "simple_test7", "examples": [simple_test7() for _ in range(5000)]},
        {"name": "simple_test8", "examples": [simple_test8() for _ in range(5000)]},
        {"name": "simple_test9", "examples": [simple_test9() for _ in range(5000)]},
        {"name": "simple_test10", "examples": [simple_test10() for _ in range(5000)]},
        {"name": "simple_test11", "examples": [simple_test11() for _ in range(5000)]},
    ]
    testing = [get_task(item) for item in testing_examples]

    # EC iterate

    generator = ecIterator(grammar,
                           training,
                           testingTasks=testing,
                        #    noConsolidation=True,
                           **args)
    for i, _ in enumerate(generator):
        print('ecIterator count {}'.format(i))