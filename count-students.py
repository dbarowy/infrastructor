import sys
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Compare one student list against an authoritative list; identify missing and extraneous student IDs')
    parser.add_argument('authoritative_list', type=str,
                        help='file name for complete list of students')
    parser.add_argument('test_list', type=str,
                        help='file name for test list of students')

    args = parser.parse_args()

    allnames = set()
    with open(args.authoritative_list, "r") as fin:
        for line in fin:
            allnames.add(line.strip().casefold())

    names = []
    with open(args.test_list, "r") as fin:
        for line in fin:
            names.extend(line.strip().split(","))
    names = [name.casefold() for name in names]
    unique = set(names)    
    duplicates = [name.casefold() for name in names if names.count(name) > 1]
    print("There are {} unique student names in {}:".format(len(unique),
                                                            args.test_list))
    print(names)
    print("missing students: ")
    missing = allnames - unique
    for student in missing:
        print(student)
    print("extra students:")
    print(unique - allnames)
    print("duplicate students:")
    print(duplicates)
