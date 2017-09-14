 Current methodology for parsing the taxonomy dumps from NCBI could be improved.

Currently this is done for two steps.

1. Take ```names.dmp``` and use grep to trim this file to only contain scientific names. The resulting file is called ```trimmed.names.dmp```.
2. This file is then passed to a python script ```make_taxonomy_pickle.py```.

I guess the author assumed that grep would be fast.

However, this creates some issues.

- Multiple file writes (time and disk)
- Functionally, of parsing the the taxonomy tree is spread out between ```base_install.sh``` and ``make_taxonomy_pickle.py``` rather than be concentrated in one place.
- It actually slower than doing the parsing in the ```make_taxonomy_pickle.py```.

### Results:

```
time grep 'scientific name' names.dmp > trimmed.names.dmp

real    0m6.857s
user    0m3.663s
sys     0m2.986s
```

and then

```
time ./test.py  # Reading trimmed.names.dmp

real    0m3.187s
user    0m2.753s
sys     0m0.369s
```

The total wall time is ```10.044s```

```test.py``` contains the following code from ```make_taxonomy_pickle.py```:

```
TRIMMED_NAMES_PATH = 'trimmed.names.dmp'
names = {}
with open(TRIMMED_NAMES_PATH) as taxonomy_names_file:
    for line in taxonomy_names_file:
            column = line.split('|')
            names[int(column[0].strip())] = column[1].strip()
```

If we update this code to skip lines which contain 'scientific name':

```
TRIMMED_NAMES_PATH = 'names.dmp'
names = {}
with open(TRIMMED_NAMES_PATH) as taxonomy_names_file:
    for line in taxonomy_names_file:
        if 'scientific name' in line: # Skip scientific names.
            column = line.split('|')
            names[int(column[0].strip())] = column[1].strip()
```

We get the following times:

```
time ./test.py # Reading names.dmp and skipping lines with 'scientific name'

real    0m3.738s
user    0m3.246s
sys     0m0.405s
```

This is 3.738s seconds faster and does not require any disk writes or reads.
