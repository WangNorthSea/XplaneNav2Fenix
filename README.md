## What is this
A script which converts X-plane12 navigation data to navdata used by Fenix Simulations A320 and insert the data to Fenix's database(nd.db3)
## How to use
Simply run the script by 'python xp_to_fenix.py'
## Things to do before you run it
1. Modify all the paths in the code to fit your own data.
2. 'db' is the path of Fenix navigation database. You are recommended to do a backup before running this script.
3. 'src_db' is used to export some old data. You can remove it and code related to it from this script if you don't need it. Just use the code in the branch of 'src_rec == None'.
## This is far from perfect
'earth_hold.dat', 'earth_msa.dat' and 'earth_mora.dat' are not converted. 
