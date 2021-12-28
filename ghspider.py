import sqlite3
import argparse
import requests
import json
import auth
import os

# Authentication headers
headers = auth.header
auth = auth.auth

'''
Function to remove the database file.
'''
def remove_db():
	try:
		os.remove('spider.db')
		print('Database file spider.db successfully deleted.')
		exit()
	except FileNotFoundError:
		print("Database file doesn't exist.")
		exit()

'''
Function to dump data for network error.
'''
def network_error():
		print('\nNetwork Connection Error.')
		print('\nPlease check your network connection.')
		print('\nYou can always restart using python3 spider.py')

'''
Function to check whether the given username is valid or not.
If response status code will be 200, then the given username is valid,
otherwise not.
'''
def check_user(user):
	try:
		url='https://api.github.com/users/'+user
		req=requests.get(url,auth=auth, headers=headers)
		if req.status_code == 200 :
			return True
		else:
			return False
	except requests.ConnectionError:
		network_error()
	except:
		print('Program Stopped.')

'''
Function for database connection.
'''
def connection():
	conn=sqlite3.connect('spider.db', isolation_level=None)
	global cur, cur2
	cur=conn.cursor()
	cur2=conn.cursor()

'''
Function to return the number of rows present in the users table.
'''
def check():
	cur2.execute('SELECT COUNT(*) FROM users')
	count=cur2.fetchone()[0]
	return count

'''
Function to spider following and followers account.
'''
def follow(uname, follow):
	url='https://api.github.com/users/'+uname+'/'+follow
	req=requests.get(url,auth=auth, headers=headers)
	res=json.loads(req.text)
	for i in res:
		if check() < num:
			cur.execute('''INSERT OR IGNORE INTO users(username) VALUES (?)''', (i['login'],))
		else:
			break

'''
Function to spider the username present in the table according to accessed.
'''
def spider():
	try:
		while True:
			try:
				cur.execute('SELECT username FROM users WHERE accessed=0')
				row=cur.fetchone()
				if(row is None):
					print('\nWow! Spidering completed')
					print('Total',check(), 'usernames spidered')
					break

				uname=row[0]
				# Printing the currently accessing username
				print('Accessing ', uname)

				url='https://api.github.com/users/'+uname
				req=requests.get(url,auth=auth, headers=headers)
				res=json.loads(req.text)
				try:
					cur.execute('''UPDATE users SET name=?,public_repos_count=?,followers_count=?, following_count=? 
					WHERE username=?''', (res['name'],res['public_repos'],res['followers'],res['following'], uname))
				except KeyError:
					print('Github API rate limit exceeded')
					exit()

				follow(uname, 'followers')
				follow(uname, 'following')

				cur.execute('''UPDATE users SET accessed=1 WHERE username=?''', (uname,))
			except sqlite3.OperationalError:
				print('Please first start the program with a valid username.')
				exit()
	except requests.ConnectionError:
		print('\nNetwork Connection Error.')
		print('\nPlease check your network connection.')
		print('\nYou can always restart using python3 spider.py')
	except KeyboardInterrupt:
		print('\nStopped by the user.')

'''
Function for initializing argparse.
'''
def parse_args():
	parser=argparse.ArgumentParser("Spider Github user's data")
	parser.add_argument('-u', '--user', help="Username to spider")
	parser.add_argument('-n', '--number', help="Number of usernames to spider", type=int, default=250)
	parser.add_argument('-r', '--remove', help="Delete database file", action='store_true')
	return parser.parse_args()

'''
Start function to drop and create table for storing the spidered data.
'''
def start(uname):
	cur.executescript('''
	DROP TABLE IF EXISTS users;
	CREATE TABLE users (
	username VARCHAR(40) UNIQUE NOT NULL,
	name TEXT,
	public_repos_count INTEGER,
	followers_count INTEGER,
	following_count INTEGER,
	accessed INTEGER DEFAULT 0
	)''')
	cur.execute('''INSERT INTO users(username) VALUES (?)''', (uname,))
	spider()

'''
main() function
'''
def main():
	args=parse_args()
	
	remove=args.remove
	if remove is True:
		remove_db()

	user=args.user
	global num
	num=args.number
	connection()
	
	if user is not None:
		if not check_user(user) :
			print("You've entered Incorrect Username.")
			print("\nPlease enter Correct Username.")
			exit()
		else:
			start(user)
	else:
		spider()

if __name__ == "__main__":
	main()
