# How to be sure two folders have exactly the same contents?

Get SHA1 sum of every file in the current tree:

	find . -type f -print0  | xargs -0 sha1sum

	...

	a58c2b2f2b1dad1ca0d8902fe43a9b2c97769d62  ./src.bak/patterns/11_arith_optimizations/mult_shifts_Keil_ARM_O3.s
	0a91f5aa4f8ee143dba531b21404c0968e96f7de  ./src.bak/patterns/11_arith_optimizations/exercises.tex
	2c41af9373f05675351f0b8e550bdba16cbb7d20  ./src.bak/patterns/11_arith_optimizations/div_EN.tex
	da39a3ee5e6b4b0d3255bfef95601890afd80709  ./src.bak/patterns/02_stack/TODO_rework_listings
	50eb41bfd9f5f2e33c9b30ea7d0c30022d10beff  ./src.bak/patterns/02_stack/main_RU.tex
	d12c4a8ebf5602a5fcae304955ff5b0f1968217e  ./src.bak/patterns/02_stack/main_PTBR.tex
	08c3b5df08f266c2972a631a6a3667055d34daa1  ./src.bak/patterns/02_stack/global_args.asm
	da39a3ee5e6b4b0d3255bfef95601890afd80709  ./src.bak/patterns/02_stack/04_alloca/TODO_rework_listings

Sort all the hashes:

	find . -type f -print0  | xargs -0 sha1sum | cut -f 1 -d ' ' | sort

	...
	
	fb222a5913a195b24fe6a74837f7474d111e097e
	fb5cb776e005f2a8112d70682a6bc6d57a136093
	fbc2c620f7827f8b9c4ccdea89a0183ab9b173eb
	fccca02b32b516f049d644cd7ae49189b2a991d7
	fdc12789a1d8ed9b824d9684c4b0c1b3b4dd7cc8

Get SHA1 sum of the list of sorted hashes:

	find . -type f -print0  | xargs -0 sha1sum | cut -f 1 -d ' ' | sort | sha1sum

This is how we getting hash of the whole directory, which can be compared with other.
Sort must be performed, because files of two equal directories can be listed in different order.

This is very close to Merkle tree, it's how hash of a torrent is calculated.

