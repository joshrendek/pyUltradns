--- Requirements ---
1. Python
2. pyOpenSSL

=== pyOpenSSL ===
Download and install pyOpenSSL...
URL: http://sourceforge.net/project/showfiles.php?group_id=31249&package_id=23298&release_id=678299
extract it and then from command line run python setup.py build (if you have trouble read the docs for it)

I ran into an error when trying setup.py build - it was complaining about missing python headers (Python.h)
-- answer was to do yum install python-devel

Then run python setup.py install to finish

-- Usage --
For mass import example see domains.test.txt
For individual commands and more usage examples run the python script with no options

