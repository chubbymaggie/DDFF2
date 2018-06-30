#!/usr/bin/python
#-*- coding: utf-8 -*-

# DDFF - Duplicate Directories and Files Finder
# by dennis(a)yurichev.com

# python >= 2.7

# knobs, available to end-user:
# PARANOID = calculate full hashes (slow)
PARANOID=False
# suppress all items below this threshold:
LIMIT=1000000 # 1MB
#LIMIT=100000 # 100Kb

import os, hashlib, pickle, sys

import math
from collections import Counter

# from https://rosettacode.org/wiki/Entropy#Python
def entropy(s):
    p, lns = Counter(s), float(len(s))
    return -sum( count/lns * math.log(count/lns, 2) for count in p.values())

all=[]
fileinfo={}

HASHBLOCK=4096
BLOCKS=5

def calc_full_hash(fname):
    #print fname
    BLK_SIZE=1024*1024
    f=open(fname, "rb")
    m=hashlib.sha256()
    while True:
        blk=f.read(BLK_SIZE)
        m.update(blk)
        if len(blk)<BLK_SIZE:
            break
        #print "."
    f.close()
    #print m.hexdigest()
    return m.hexdigest()

# fileinfo item = tuple (fsize, mtime, hexdigest, full)
# full = True if full hash, False if partial
# full variable never used after... but anyway...
def file_calc_hash (fname):
    global fileinfo
    global all
    mtime=os.stat(fname).st_mtime
    if fname in fileinfo:
        if fileinfo[fname][1]==mtime:
            all.append((False, fname, fileinfo[fname][0], fileinfo[fname][2]))
            #print fileinfo[fname]
            return fileinfo[fname][0],fileinfo[fname][2]
    fsize=os.path.getsize(fname)
    if fsize < HASHBLOCK*BLOCKS or PARANOID:
        hexdigest=calc_full_hash(fname)
        full=True
    else:
        # calc partial hash:
        f=open(fname, "rb")

        m=hashlib.sha256()
        blk=""
        for b in range(BLOCKS):
            f.seek((fsize/BLOCKS)*b, os.SEEK_SET)
            blk=blk+f.read(HASHBLOCK)
        f.close()

        full=False
        m.update(blk)
        hexdigest=m.hexdigest()

        e=entropy(blk)
        if e<7:
            # entropy level is too low, calculate full hash
            hexdigest=calc_full_hash(fname)
            full=True
            #print "calculating full hash", fname, fsize, e

    all.append((False, fname, fsize, hexdigest))
    fileinfo[fname]=(fsize, mtime, hexdigest, full)
    return fsize, hexdigest

dirs_processed=0

def dir_calc_hash(d):
    global all, dirs_processed
    hashes=[]
    dirsize=0
    tmp=os.listdir(d)
    return_None=False

    for t in tmp:
        if d.endswith("/"):
            t2=d+t
        else:
            t2=d+"/"+t
        if os.path.islink(t2):
            continue
        if os.path.isfile(t2):
            #print "file", t2, file_calc_hash(t2)
            try:
                fsize, hash=file_calc_hash(t2)
                hashes.append(hash)
                dirsize=dirsize+fsize
            except OSError:
                print "OSError:", t2
                return_None=True
            except IOError:
                print "IOError:", t2
                return_None=True
        if os.path.isdir(t2):
            #print "dir", t2, dir_calc_hash(t2)
            try:
                dsize, hash=dir_calc_hash(t2)
                if hash==None:
                    return_None=True
                else:
                    hashes.append(hash)
                    dirsize=dirsize+dsize
            except OSError:
                print "OSError:", t2
                return_None=True
            except IOError:
                print "IOError:", t2
                return_None=True

    # error while reading file or calculating dir hash, hence, hash of a parent dir wouldn't be calculated as well!
    if return_None:
        return None, None
    hashes.sort()
    m=hashlib.sha256()
    m.update("".join(hashes))
    all.append((True, d, dirsize, m.hexdigest()))
    dirs_processed=dirs_processed+1
    if (dirs_processed % 100)==0:
        print "heartbeat, dirs_processed=", dirs_processed, "dir just finished=", d
    return dirsize, m.hexdigest()

# "/home/dennis/tmp" -> "/home/dennis" or None if input path can't be "chopped" further
def chop_path_element_right(p):
    #if p.endswith("/"):
    #    p=p[:-1]
    t=p.split("/")
    t=filter(None, t) # https://stackoverflow.com/questions/3845423/remove-empty-strings-from-a-list-of-strings
    if len(t)<=1:
        return None
    return "/"+"/".join(t[:-1])

# find fname/path among [already] dumped items
# "chop" the path by one item, until it can be found in dumped[]
def find_among_dumped(dumped, a):
    while True:
        if a in dumped:
            return True
        new_a=[]
        #print "a", a
        for t in a.split(";"):
            #print "chop in", t
            t=chop_path_element_right(t)
            #print "chop out", t
            if t==None:
                return False
            new_a.append(t)
        new_a=";".join(new_a)
        #print "new_a", new_a
        a=new_a

def nice_size(s):
    s=float(s)
    if s>1000000000:
        return "%.1fGB" % (s/1000000000)
    if s>1000000:
        return "%.1fMB" % (s/1000000)
    if s>1000:
        return "%.1fKb" % (s/1000)
    return "%d" % s

def dump_all():
    d={}
    for a in all:
        t=(a[0], a[2], a[3]) # entry type, size, digest
        if t not in d:
            d[t]=[]
        d[t].append(a[1])

    # d{} dict at this point is:
    # key=tuple (entry type, size, digest)
    # value=list of (paths/filenames)

    results=[]

    # add to results[] only what has len(list)>1, i.e., can be duplicate
    for a in d:
        if len(d[a])>1:
            if a[0]==False:
                results.append(("file", a[1], d[a]))
            else:
                results.append(("dir", a[1], d[a]))

    # results=list of tuple (type, size, path/filename)

    # sort results by file/dir size:
    results.sort(key=lambda x: x[1], reverse=True)

    results_dumped=set()

    f=open("ddff.txt", "wt")
    for r in results:
        if r[1]<LIMIT:
            break
        if find_among_dumped(results_dumped, ";".join(sorted(r[2]))):
            #f.write ("this is going to be suppressed:\n")
            continue
        f.write("* "+r[0]+" size="+nice_size(r[1])+"\n")
        for x in r[2]:
            f.write(x+"\n")
        f.write("\n")
        t=";".join(sorted(r[2]))
        #print t
        results_dumped.add(t)
    f.write ("")
    f.close()
    print "the report file 'ddff.txt' has been written"
    
print "DDFF - Duplicate Directories and Files Finder"
print "by dennis(a)yurichev.com"
print ""

dirs=sys.argv[1:]
if len(dirs)==0:
    print "usage: ddff.py <dir1> <dir2> ... etc"
    print "dir can be '~', '/', etc"
    exit(0)

try:
    print "loading db data from ddff.db"
    f=open("ddff.db", "rb")
    fileinfo=pickle.load(f)
    f.close()
    print "db data loaded"
except IOError:
    pass
except EOFError:
    pass

interrupted=False
try:
    for d in dirs:
        p=os.path.expanduser(d) # handle ~
        p=os.path.realpath(p) # handle dots
        print "scanning and processing", p
        dir_calc_hash(p)

    dump_all()

except KeyboardInterrupt:
    print "shutting down gracefully."
    interrupted=True

print "saving db data for future use. please wait. don't interrupt."
if interrupted==False:
    print "The 'ddff.txt' report file is ready and can be browsed."
f=open("ddff.db", "wb")
pickle.dump(fileinfo, f)
f.close()
print "db data saved to ddff.db"

