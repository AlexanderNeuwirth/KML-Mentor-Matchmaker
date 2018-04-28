
"""

Code written/adapted by Alexander Neuwirth, July 2017

Built off of a charity Valentine's Day matchmaking program written by a variety of
authors, mainly Matthew Hughes, with some degree of assistance from Alexander Neuwirth,
Andrew Hughes, and various members of the 2015-2016 KML Software Development Club.

Significant revisions and additions were made by Xander Neuwirth about 18 months later,
repurposing the program for use in the Cross Trainers mentor program.

As the following code is built hackily atop another program, certain areas are likely
to be messy or redundant.

This code is not formally licensed in any way, but it is intended to be used by the Cross Trainers
organization at Kettle Moraine Lutheran high school, or whatever associated program may serve
its equivalent purpose in matching incoming freshmen with student mentors. As such,
use of this program or its contents for another purpose including (but not limited to)
profitable enterprises of any sort is strictly prohibited, by whatever legal protection
this intellectual property can secure.

Please contact Alexander Neuwirth at alexander.e.neuwirth@gmail.com for inquiries
related to this software.

"""

from random import choice
from random import randint
import random
import os
import shutil
import csv
import string
import operator
import sqlite3
import time
import copy
#import difflib # To fix (SOME) minor spelling asynchrocies and formatting anomalies
from jinja2 import Environment, PackageLoader


# Percent match is relative to this number of interests
# (par*2 = 200%) Really only makes cosmetic difference
INTEREST_PAR = 5

CALCULATE_REPORT = True
PRINT_REPORT = True
INTEREST_REPORT = True
INDIVIDUAL_REPORTS = False
ODDBALL_REPORTS = True
MASTER_REPORT = True
PATCH_MISSING_MATCHES = True # True # ENABLE for official runs
PRIORITIZE_GENDER_PICKY = True
PRIMARY_REPORT = True
MENTOR_REPORT = True


render_data = [] # Collection of calculated data to pass to rendering
#chicks = [] # Eventual storage of reformatted data
#guys = []   # For use in random-data-gen debugging
mentors = []
mentees = []
mentor_matches = {} # Populated with {mentor:mentee} entries

MALE = "MALE"
FEMALE = "FEMALE"
YES = "YES"
NO = "NO"

#### JINJA:
env = Environment(loader=PackageLoader('match', 'templates'))


class Person:
	def __init__(self):
		self.first_name = "BOB"
		self.last_name = "EVANS"
		self.sex = "SAUSAGE"
		self.school = "KETTLE MORAINE LUTHERAN HIGH SCHOOL"
		self.gender_picky = True # requests to be matched with same gender
		self.is_mentor = False
		self.answers = []
		self.grade = 10
		self.id = -1
		self.matches = {}
		self.valid_matches = []
		self.friend_matches = []
		self.avg_rank = 0
		self.avg_score = 0
		
	def from_row(self, row):
		self.id = row[0]
		self.first_name = row[1]
		self.last_name = row[2]
		self.sex = row[3]
		self.school = row[4]
		self.gender_picky = row[5]
		self.is_mentor = row[6]
		
	def save_student(self, db):
		if self.id < 0:
			student_cmd = """
			INSERT OR REPLACE INTO students
			(fname, lname, sex, school, gender_picky, is_mentor) VALUES
			(:fname, :lname, :sex, :school, :gender_picky, :is_mentor);"""
		
			
			db.execute(student_cmd,	{ 
				"fname":self.first_name,
				"lname":self.last_name,
				"sex":1 if self.sex == MALE else 2,
				"school":self.school,
				"gender_picky":self.gender_picky,
				"is_mentor":1 if self.is_mentor else 0
			})
			self.id = db.lastrowid
		else:
			student_cmd = """
			INSERT OR REPLACE INTO students
			(id, fname, lname, sex, school, gender_picky, is_mentor) VALUES
			(:id, :fname, :lname, :sex, :school, :gender_picky, :is_mentor);"""
		
			
			db.execute(student_cmd,	{ 
				"id":self.id,
				"fname":self.first_name,
				"lname":self.last_name,
				"sex":1 if self.sex == MALE else 2,
				"school":self.school,
				"gender_picky":self.gender_picky,
				"is_mentor":self.is_mentor
			})
			
	def get_name(self):
		return self.first_name + " " + self.last_name
		
	def save_answers(self, db):
		answers_cmd = """
		INSERT OR REPLACE INTO answers
		(student_id, question_id, value) VALUES
		(:student_id,:question_id,:value);"""
		
		question_id = 0
		for answer in self.answers:
			db.execute(answers_cmd,{
				"student_id":self.id,
				"question_id":question_id,
				#"value":"ABCD".index(answer)})
				"value":answer}) # Attempt to patch non-labeled question issues
			question_id+=1

class RenderData:
	def __init__(self,target,top_matches=[],friend_matches=[],least_compatible_matches=[]):
		self.target = target
		self.top_matches = top_matches
		self.friend_matches = friend_matches
		self.least_compatible_matches = least_compatible_matches

class Match:
	def __init__(self):
		self.person = Person()
		self.owner = Person()
		self.score = 0.0
		self.friend_mode = False
		self.rank = 0
		
	def compare(matchA, matchB):
		if matchA.score > matchB.score:
			return -1
		if matchA.score == matchB.score:
			return 0
		if matchA.score < matchB.score:
			return 1
		
	def get_string(self):
		return self.owner.first_name +" "+ self.owner.last_name + " and " + self.person.first_name + " " + self.person.last_name


def opendb(in_memory):
	db_create = ["""CREATE TABLE IF NOT EXISTS students
	( id INTEGER PRIMARY KEY AUTOINCREMENT, fname text, lname text, sex integer, school text, gender_picky integer, is_mentor integer);""",
	#TODO: make gender_picky use int to be fancier

	"""CREATE TABLE IF NOT EXISTS answers
	( student_id integer, question_id integer, value str);""" ]
	
	con = sqlite3.connect(":memory:" if in_memory else "matchmaker.db")
	con.text_factory = str
	cur = con.cursor()
	for cmd in db_create:
		cur.execute(cmd)
	return cur

def load():
	mentees = []
	mentors = []
	with open("mentors.csv", "r") as csvfile:
		scanner = csv.reader(csvfile, delimiter=',')
		offset = 0
		for row in scanner: # Loops through rows read from csv file
			row_person = Person()
			
			row_person.first_name = row[0]
			row_person.last_name = row[1]
			row_person.school = row[4]#"".join(e for e in row[4].upper() if e.isalnum())
			row_person.is_mentor = True
			
			if row[2].upper() == MALE:
				row_person.sex = MALE
			else:
				row_person.sex = FEMALE
			
			if row[3].upper() == YES:
				row_person.gender_picky = True
			else:
				row_person.gender_picky = False
			
			offset = 5
			addition_list = []
			INTEREST_PAR = len(row) - offset - 1
			for i in range(offset,len(row)): # Puts multiple choice answers into a list
				interest_string = row[i].upper()
				raw_interest_list = interest_string.split(", ")
				interest_list = []
				for raw_interest in raw_interest_list: # strip spaces and special characters to maximize matches
					interest = ("".join(e for e in raw_interest if e.isalnum()))
					if interest != "":
						interest_list.append(interest)
				addition_list += interest_list
			row_person.answers = addition_list
			
			mentors.append(row_person)
	pass
	with open("mentees.csv", "r") as csvfile:
		scanner = csv.reader(csvfile, delimiter=',')
		offset = 0
		for row in scanner: # Loops through rows read from csv file
			row_person = Person()
			
			row_person.first_name = row[0]
			row_person.last_name = row[1]
			row_person.school = row[4] #"".join(e for e in row[4].upper() if e.isalnum()) # for formatting strip
			
			if row[2].upper() == MALE:
				row_person.sex = MALE
			else:
				row_person.sex = FEMALE
			
			if row[3].upper() == YES:
				row_person.gender_picky = True
			else:
				row_person.gender_picky = False
				
			row_person.is_mentor = False
			
			offset = 5
			addition_list = []
			INTEREST_PAR = len(row) - offset - 1
			for i in range(offset,len(row)): # Puts multiple choice answers into a list
				interest_string = row[i].upper()
				raw_interest_list = interest_string.split(", ")
				interest_list = []
				for raw_interest in raw_interest_list: # strip spaces and special characters to maximize matches
					interest = ("".join(e for e in raw_interest if e.isalnum()))
					if interest != "":
						interest_list.append(interest)
				addition_list += interest_list
			row_person.answers = addition_list
			
			mentees.append(row_person)
	pass
	return mentees + mentors

def get_fudge(): # Unused because it's immoral
	return 0
	#upper = (1./(INTEREST_PAR+1))/2
	#fudge = (random.random())*upper
	# print "{:3.4f}".format(fudge)
	#return fudge

def sanitize_name_list(name_list):
	length = len(name_list)
	for index in range(length):
		name = name_list[index]
		name = name.split()[0]
		name_list[index] = name

# Used to populate test data when necessary. Requires some modification for actual use.
def random_data_generator(number_of_men = 200, number_of_women = 200, number_of_questions = 22, answers=['A','B','C','D']):
	man_names = open("census-dist-male-first.txt","r").readlines()
	sanitize_name_list(man_names)
	woman_names = open("census-dist-female-first.txt","r").readlines()
	sanitize_name_list(woman_names)
	last_names =open("census-dist-2500-last.txt","r").readlines()
	sanitize_name_list(last_names)
	people = []
	for random_guy in range(number_of_men):
		man = Person()
		man.first_name = choice(man_names)
		man.last_name = choice( (
			choice(man_names+woman_names)+"SSON", 
			choice(last_names)))
		man.sex = MALE
		man.answers =[choice(answers) for i in range(number_of_questions)]
		people.append(man)
	for random_chick in range(number_of_women):
		woman = Person()
		woman.first_name = choice(woman_names)
		woman.last_name = choice((
			choice(man_names+woman_names)+"DOTTIR", 
			choice(last_names)))
		woman.sex = FEMALE
		woman.answers =[choice(answers) for i in range(number_of_questions)]
		people.append(woman)
	return people

def clamp(value):
	if value > 100:
		return 100
	elif value < 0:
		return 0
	else:
		return value

def report(person, valid_matches, friend_matches):
    if True: #PRINT_REPORT:
    	print ("PERSON: {fname} {lname}".format(
    		fname=person.first_name,
    		lname=person.last_name))
    	print("---------------------")
    	print ("Valids:")
    	for valid_match in valid_matches:
    		print("{score:3.2%} {fname} {lname}".format(
    			score=valid_match.score,
    			fname=valid_match.person.first_name,
    			lname=valid_match.person.last_name))
    	print("---------------------")
    	print("Friends:")
    	for friend_match in friend_matches:
    		print("{score:3.2%} {fname} {lname}".format(
    			score=friend_match.score,
    			fname=friend_match.person.first_name,
    			lname=friend_match.person.last_name))
    	print("\n\n")
    return

def master_report(data):
	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/primary"):
		os.mkdir("output/primary")
	shutil.copy("templates/pure-min.css","output/primary/pure-min.css")
	template = env.get_template('report_template.html')
	html = template.render(data=data)
	out = open("output/primary/master.html","w")
	out.write(html)
	
	out.close()

def html_report(target, top_matches, friend_matches, least_compatible_matches): # Outdated and unused

	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/primary"):
		os.mkdir("output/primary")
	shutil.copy("templates/pure-min.css","output/primary/pure-min.css")
	template = env.get_template('report_template.html')
	student_data = []
	data = RenderData(target=target,top_matches=top_matches,
		friend_matches=friend_matches,
		least_compatible_matches=least_compatible_matches)
	student_data.append(data)
	html = template.render(
		data=student_data)
	out = open(
		"output/primary/{lname}_{fname}.html".format(
			lname=target.last_name,
			fname=target.first_name),"w")
	out.write(html)
	
	out.close()

def oddball_report(target, students):

	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/oddball"):
		os.mkdir("output/oddball")
		
	shutil.copy("templates/pure-min.css","output/oddball/pure-min.css")
	template = env.get_template('oddball_report_template.html')

	avg_rank = target.avg_rank
	avg_score = target.avg_score
	

	html = template.render(
		target=target,
		students=students,
		avg_rank=avg_rank,
		avg_score=avg_score)
	out = open(
		"output/oddball/{lname}_{fname}.html".format(
			lname=target.last_name,
			fname=target.first_name),"w")
	out.write(html)
	out.close()

def rawSQL(string):
	db.execute(string)
	rows = db.fetchall()
	return rows

def student_query(db, student, sex=MALE, limit=10, isDescending=True):
	"""
	This query returns matches for a student with a given sex, limit and ordering 
	"""
	
	cmd = """
	SELECT a1.student_id as a1id, a2.student_id as a2id, s.grade, COUNT(*) as score
		FROM answers AS a1
		INNER JOIN answers as a2 
			ON a1.student_id IS NOT a2.student_id AND a1.question_id IS a2.question_id AND a1.value IS a2.value  
		INNER JOIN students as s
			ON s.id IS a2.student_id
		WHERE s.sex IS :sex AND a1id IS :student_id
		GROUP BY a2.student_id
		ORDER BY a1id, score DESC
		LIMIT :limit
		"""
		
	db.execute(cmd,	{ 
		"student_id":student.id,
		"sex" : 1 if sex is MALE else 2,
		"limit":limit,
		"direction":"DESC" if isDescending else "ASC" }	)
		
	rows = db.fetchall()
	
	return rows

def master_query(db):
	"""
	This query returns every match for every student within the database
	"""
	
	old_cmd = """
	SELECT a1.student_id as a1id, a2.student_id as a2id, COUNT(*) as score
		FROM answers AS a1
		INNER JOIN answers as a2 
			ON a1.student_id IS NOT a2.student_id AND a1.question_id IS a2.question_id AND a1.value IS a2.value  
		INNER JOIN students as s
			ON s.id IS a2.student_id
		GROUP BY a2.student_id, a1.student_id
		"""
	
	cmd = """
	SELECT a1.student_id as a1id, a2.student_id as a2id, COUNT(*) as score
		FROM answers AS a1
		INNER JOIN answers as a2 
			ON a1.student_id IS NOT a2.student_id AND a1.value IS a2.value  
		INNER JOIN students as s
			ON s.id IS a2.student_id
		GROUP BY a2.student_id, a1.student_id
		"""
	
	db.execute(cmd)
		
	rows = db.fetchall()
	return rows

def get_student(id):
	"""
	This query returns a row representing a student with the given id
	"""
	
	db.execute("SELECT * FROM students WHERE id = :id",{"id":id})
	first = db.fetchone()
	return first

def mentor_report(pairs, date, unmatched_mentors, unmatched_mentees):
	reversed_pairs = {v: k for k, v in pairs.iteritems()}
	# to make mentor lookup by mentee possible
	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/mentor"):
		os.mkdir("output/mentor")
	shutil.copy("templates/pure-min.css","output/mentor/pure-min.css")
	template = env.get_template('mentor_report_template.html')
	html = template.render(
		pairs=pairs,
		reversed_pairs=reversed_pairs,
		date=date,
		unmatched_mentors=unmatched_mentors,
		unmatched_mentees=unmatched_mentees)
	out = open("output/mentor/report.html","w")
	out.write(html)
	
	out.close()

"""
The following function defines the mentor/mentee drafting process.
It goes through the match data, picking out the top-scored valid match.

It then adds the match to the finalized matches dict, removes the match
participants from the working dict, and restarts the process until either all
mentees or all mentors have been paired.

It will then return a list of unpaired mentors or mentees. #TODO: Handle this nicely
"""
def draft_pairs(students = {}):
	working_dict = students
	#print working_dict
	found_gender_picky = True
	best_match = None
	
	# This doesn't work, but hasn't become necessary yet. It should be salvageable if it becomes necessary to use.
	"""for key in working_dict:
		# Minimizes impossible matches by prioritizing students with only one valid match
		student = working_dict[key]
		student.valid_matches = sorted(student.valid_matches,cmp=Match.compare)
		if len(student.valid_matches) == 1:
			print "Prevented " + student.get_name() + " from having no valid matches by forcing a match with " + student.valid_matches[0].person.get_name()
			student.valid_matches[0].score = 100000000 # Ensures this match is selected, as it is the only valid match
			best_match = student.valid_matches[0]""" 


	if PRIORITIZE_GENDER_PICKY:
		for key in working_dict:
			student = working_dict[key]
			student.valid_matches = sorted(student.valid_matches,cmp=Match.compare)
			if student.gender_picky == 1:
				for match in student.valid_matches:
					if best_match == None:
						best_match = match
					elif match.score > best_match.score:
						best_match = match
	if best_match == None: # Runs if gender picky prioritization is off or no gender picky is found
		found_gender_picky = False
		for key in working_dict:
			
			student = working_dict[key]
			student.valid_matches = sorted(student.valid_matches,cmp=Match.compare)
			for match in student.valid_matches:
				if best_match is None:
					best_match = match
				elif match.score > best_match.score:
					best_match = match		
	
	if best_match == None: # Runs if no more valid matches exist
		return working_dict
	else: # Ensures {mentor,mentee} dict pair for orderliness
		if best_match.owner.is_mentor == 1:
			mentor_matches[best_match.owner] = best_match.person
		else:
			mentor_matches[best_match.person] = best_match.owner
			
	new_working_dict = {}
	
	
	#print working_dict[1].matches
	for entry in working_dict:
		if (working_dict[entry] != best_match.owner) and (working_dict[entry] != best_match.person):
			new_working_dict[entry] = working_dict[entry]
			new_matches = []
			
			# Loops through non-removed person's matches to look for removed people.
			# Removes matches containing removed people so they don't get caught in the next cycle
			
			for match in working_dict[entry].valid_matches:
				#print working_dict[entry].matches[match].person
				if (match.person != best_match.owner):
					if (match.person != best_match.person):
						if (match.owner != best_match.owner):
							if (match.owner != best_match.person):
								#sprint "Did not remove " + working_dict[entry].matches[match].owner.first_name + " " + working_dict[entry].matches[match].owner.last_name + " and " + working_dict[entry].matches[match].person.first_name + " " + working_dict[entry].matches[match].person.last_name + " match."
								new_matches.append(match)
					
				#else:
					#print "Removed " + working_dict[entry].matches[match].owner.first_name
			new_working_dict[entry].valid_matches = new_matches
	#print new_working_dict[1].matches
	return draft_pairs(new_working_dict) # This seems like it would return everyone 
			
def parse_main_query_rows(rows, students={}):
	"""
	This takes the output from our master_query and yields populated
	People (student) objects with matches. It also computes some basic
	global statistics for my own amusement.
	"""
	avg_score = 0
	most_popular = None
	most_compatible = None
	
	for row in rows:
		a1_id = row[0]
		a2_id = row[1]
		score = row[2]
		
		# If either student is not yet registered to students dict, register it from database
		if a1_id not in students:
			a1_student = Person()
			a1_student.from_row(get_student(a1_id))
			students[a1_id] = a1_student
		else:
			a1_student = students[a1_id]
		
		if a2_id not in students:
			a2_student = Person()
			a2_student.from_row(get_student(a2_id))
			students[a2_id] = a2_student
		else:
			a2_student = students[a2_id]
		
		
		match = Match()
		match.owner = a1_student
		match.person = a2_student
		match.score = score * 1.0 / INTEREST_PAR
		
		a1_student.matches[a2_id] = match
		if a1_student.is_mentor != a2_student.is_mentor:
			# Check if students are the same gender or don't care: if so, valid match
			if (a1_student.sex == a2_student.sex) or (((a1_student.gender_picky == 0) and (a1_student.gender_picky == 0))):
				a1_student.valid_matches.append(match)
			#else: a1_student.garbage_matches.append(match)
		else:
			a1_student.friend_matches.append(match)
		
	for key in students:
		student = students[key]
		
		student.valid_matches = sorted(student.valid_matches,cmp=Match.compare)
		student.friend_matches = sorted(student.friend_matches,cmp=Match.compare)
		
		# You are my Index[0] Baby!
		
		for match in student.valid_matches:
			match.rank = student.valid_matches.index(match)+1
		for match in student.friend_matches:
			match.rank = student.friend_matches.index(match)+1
		
		
		for key in student.matches:
			match = student.matches[key]
			student.avg_rank += match.rank
			student.avg_score += match.score
			
		student.avg_rank /= (len(students)-1)
		student.avg_score /= (len(students)-1)
		avg_score += student.avg_score
		
		if most_popular is None:
			most_popular = student
		else:
			if most_popular.avg_rank < student.avg_rank:
				most_popular = student
		if most_compatible is None:
			most_compatible = student
		else:
			if most_compatible.avg_score < student.avg_score:
				most_compatible = student
				
	avg_score /= len(students)
	
		
	return students, { 
		"avg_score":avg_score,
		"most_compatible": most_compatible,
		"most_popular": most_popular}

def interest_report(students):
	render_data = []
	
	if not os.path.exists("output"):
		os.mkdir("output")
	if not os.path.exists("output/interest"):
		os.mkdir("output/interest")
	shutil.copy("templates/pure-min.css","output/primary/pure-min.css")
	template = env.get_template('interests_template.html')
	
	html = template.render(
		data=students)
	out = open(
		"output/interest/master.html","w")
	out.write(html)
	
	out.close()

def do_html_report(students):
	"""
	This renders out the "Primary" report html docs, calling the
	html_report(...) render function on each student in the list:
	`students`
	"""
	for student in students:
		valid_list = student.valid_matches[:10]
		friend_list = student.friend_matches[:10]
		temp = [] + student.valid_matches
		temp.reverse()
		dislike_list = temp[:3]
		if INDIVIDUAL_REPORTS:
			html_report(student,valid_list,friend_list,dislike_list)
		data = RenderData(target=student,top_matches=valid_list,
			friend_matches=friend_list,
			least_compatible_matches=dislike_list)
		render_data.append(data)
		
	render_data.sort(key=lambda datum: datum.target.last_name)
	# Alphabetize render data entries by last name to make report prettier
		
	
	if MASTER_REPORT: master_report(render_data)
	# Move html_report stuff to another function
	#do_master_report(master_uber_mega_ultra_awesome_list)

if __name__ == "__main__":
	db = opendb(False) # make False to save db to disk
	
	print ("Loading data...\n")
	#ugly_people,guys,chicks = random_data_generator()
	file_people = load()
	
	for person in file_people: # Store File-People in the Database
		person.save_student(db)
		person.save_answers(db)
	
	student_count = len(file_people)
	interest_report(file_people)
	file_people = None
	
	print ("Finding Matches...\n")

	students = {}
	rows = master_query(db)
	
	"""
	The SQL query that determines matches doesn't actually log 0% matches.
	The problem is, when you have a limited sample of one gender, it doesn't find
	matches with that gender when someone don't have any activities in common with them
	If you have a incoming freshman who's gender_picky and male, but doesn't have any
	extracurriculars in common with an available male mentor, they have no valid matches
	
	The following loop remedies this by finding holes in the matches returned, and adding
	0% matches. This also makes "least compatible" more accurate, which is a fun stat.
	
	As it's somewhat CPU intensive, the loop is configurable with the PATCH_MISSING_MATCHES
	global config constant.
	
	"""
	
	if PATCH_MISSING_MATCHES:
		print("Patching missing matches...")
		for a in range(1,student_count):
			for b in range(1, student_count):
				if a != b:
					exists = False
					for match in rows:
						lmatch = list(match)
						if ((lmatch[0] == a) and (lmatch[1] == b)) or ((lmatch[1] == b) and (lmatch[1] == a)):
							exists = True
					if not exists:
						rows.append((a,b,0))
			if a%10==0:print("Patch is {:.3}% complete").format(float(a)/float(student_count) * 100)
		print "Patch complete. \n"
	
	print "Calculating compatibility...\n"
	students, stats = parse_main_query_rows(rows, students)
	
	copied_students = {}
	# This is necessary because draft_pairs() destroys the matches of student
	# objects, which need to be referenced for leftovers
	for key in students:
		student = students[key]
		copied_students.update({key:copy.copy(student)})
	
	print "Drafting pairs...\n"

	leftovers = draft_pairs(students)

	for key in leftovers: # Reloads leftover matches from backup student objects
		leftover = leftovers[key]
		leftover.valid_matches = copied_students[key].valid_matches[:10]
		
	unmatched_mentors = []
	unmatched_mentees = []
	for leftover in leftovers:
		if leftovers[leftover].is_mentor == 1:
			unmatched_mentors.append(leftovers[leftover])
		else:
			unmatched_mentees.append(leftovers[leftover])
	
	if leftovers is not None:
		print "Leftovers:"
		for student in leftovers:
			print leftovers[student].get_name() + (" (mentor)" if leftovers[student].is_mentor == 1 else " (mentee)")
		print "To minimize leftovers, set PATCH_MISSING_MATCHES to True.\n" if (not PATCH_MISSING_MATCHES) else "\n"
	else: print "No leftovers. \n"
	
	print("Statistics:")
	print("Average Score: {avg_score}".format(avg_score=stats["avg_score"]))
	print("Most Popular: {fname} {lname}".format(
		fname = stats["most_popular"].first_name, 
		lname = stats["most_popular"].last_name))
		
	print("Most Compatible: {fname} {lname}".format(
		fname = stats["most_compatible"].first_name, 
		lname = stats["most_compatible"].last_name))
	print("")
	
	print ("Caching Results...\n")
	student_list = []
	for key in students:
		student_list.append(students[key])
	
	if PRIMARY_REPORT:
		print ("Writing Primary Report\n")
		do_html_report(student_list)
	
	if INTEREST_REPORT: #This report cannot be run from this location, as interests are destroyed in the matching process
		print("Writing Interest Report\n")
		#interest_report(student_list)
	
	if ODDBALL_REPORTS:
		print ("Writing Oddball Reports\n")
		for person in student_list:
			oddball_report(person, student_list)
	
	if MENTOR_REPORT:	
		print "Writing Mentor Pair Report"
		date=time.strftime("%m/%d/%Y")
		mentor_report(mentor_matches,date,unmatched_mentors,unmatched_mentees)
		