from distutils.core import setup, Extension

module1 = Extension('safestream',
                    sources = ['safestream.c'])

setup (name = 'SafeStream',
       version = '0.1',
       description = 'An implementation of BytesIO that zero-fills all allocated memory to prevent forensic recovery',
       ext_modules = [module1])
