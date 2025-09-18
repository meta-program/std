from setuptools import setup

if __name__ == "__main__":
    setup(package_data={
        '': [
            'lib/eigen.dll',
            'lib/libeigen.so',
            'assets/cn/segment/vocab.csv',
            'assets/jp/segment/vocab.csv',
            'cpp/rabin_karp.cpp',
            'cpp/Makefile',
            'src/std/utility.h',
            'src/std/utility.cpp',
            'src/hash/HashCode.h',
            'src/hash/HashCode.cpp',
            'src/hash/Matches.h',
            'src/hash/Matches.cpp',
            'src/hash/RabinKarp.h',
            'src/hash/RabinKarp.cpp',
        ],
    })

# usage of twine:
# pip install twine
# python setup.py install
# pip uninstall -y std.algorithm && pip install --upgrade --no-cache-dir std.algorithm
# pip install --upgrade --retries=50 std.algorithm -i https://pypi.Python.org/simple/