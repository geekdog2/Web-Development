DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Questions;
DROP TABLE IF EXISTS LinkClicks;
DROP TABLE IF EXISTS Assessments;
DROP TABLE IF EXISTS Questions;
DROP TABLE IF EXISTS studentAttempts;
DROP TABLE IF EXISTS allAttempts;
DROP TABLE IF EXISTS Comments;

CREATE TABLE allAttempts(
	'id' INTEGER PRIMARY KEY AUTOINCREMENT,
	'assessmentid' INTEGER NOT NULL,
	'username' TEXT NOT NULL,
	'completed' TEXT,
    'count' INTEGER NOT NULL DEFAULT 0,
	'mark' INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE Comments
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER,
    created    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usertype VARCHAR(30),
    username VARCHAR(30),
    content    TEXT BOT  NULL
);

CREATE TABLE studentAttempts(
	'assessmentid' INTEGER NOT NULL,
	'username' TEXT NOT NULL,
	'completed' TEXT,
    'count' INTEGER NOT NULL DEFAULT 0,
	'mark' REAL NOT NULL DEFAULT 0.00
);

CREATE TABLE Assessments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT BOT NULL,
    content TEXT BOT NULL,
    type TEXT CHECK (type IN ('formative', 'summative'))
);

CREATE TABLE Questions(
    'assessmentid' INTEGER,
	'id' INTEGER PRIMARY KEY AUTOINCREMENT,
	'question' TEXT  NOT NULL,
	'answer' TEXT NOT NULL,
	'check1' TEXT NOT NULL,
	'check2' TEXT NOT NULL,
	'check3' TEXT,
	'feedback' TEXT NOT NULL,
	'comment' TEXT
);	

CREATE TABLE LinkClicks (
    id INTEGER PRIMARY KEY,
    link VARCHAR(255) NOT NULL,
    clicks INTEGER DEFAULT 0
);


CREATE TABLE IF NOT EXISTS 'Users' (
'usertype' VARCHAR(30),
'id' INTEGER,
'password' VARCHAR(50)
);


INSERT INTO Users (usertype, 
	id, password) VALUES (
	'Student', 123,'1');

INSERT INTO Users (usertype,
	id, password) VALUES (
	'Teaching-staff', 123,'1');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 2,
	'Which one of the following is not a Java feature?', 'Use of pointers',
	'Object-oriented', 'Portable', 'Dynamic and Extensible',
	"Pointers are are not features of Java due to security concerns. A variable can be accessed anywhere within the program if you have it's address, even if it's private",
	 'this is a comment' );

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 2,
	'What is the extension of Java code files?', '.java',
	'.js', '.txt', '.class', 
	'The extenions for Java code files is .java, .js is for JavaScript files, .txt for text files and .class for class files.', 
	'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 2,
	'Which of these cannot be used for a variable name in Java?', 'keyword',
	'identifier & keyword', 'identifier', 'none mentioned',
	'Any keywords or reserved words cannot be used as variables in Java. Some of these include for, if, static and int.',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'Which of the following is the correct way to define an initializer method?', 'def __init__(self, title, author):',
	'def __init__(title, author):', 'def __init__():', '__init__(self, title, author):', 
	' The "self" is an instance of the provided class and the parameters will be used to initialize variables.',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'The _________ keyword defines a template indicating the data that will be in an object of the class and the functions that can be called on an object of the class',
	'class', 'object', 'Class', 'instance', 'The class keyword defines the data that is in an object of a class and the functions that can be called on an object of the class.',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'Which type of Programming does Python support?', 'all of the mentioned',
	'object-oriented', 'structured ', 'functional ', 'Python is an interpreted programming language and it supports all the features listed above ',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'When a function is defined inside a class, what is it called?', 'Method',
	'Module', 'Class ', 'Another Function ', 
	'When this occrus the function becomes a method. The method can be accessed by data inside the class.',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'Which of the answers below describes the use of id() function in python?', 'Id returns the identity of the object',
	'Every object doesn’t have a unique id', 'All mentioned ', 'None mentioned ', 
	'Every object in python has an id unique assigned to it, which is returned with the id() function',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'What is the output of the expression : 6*2**2', '24',
	'144', '78 ', '82 ', 
	'The precendence of ** is higher than that of *, and so 6**2 will be carried out first and then the answer will be multiplied',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'If a function does not return a value, what value is shown when executed at the shell?', 'None',
	'int', 'bool ', 'void ', "If no value is specified then python will define the None object that's returned",
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'Which module in Python supports regular expressions?', 're',
	'regex', 'pyregex ', 'None mentioned ', 
	're can be imported using: import er. This is because re is a part of the standard library',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'Of those below, which is one is not a complex number?', 'f = 7 + 2l',
	'f = 9 + 1a', 'f = complex(11, 5) ', 'f = 7 + 23J ', 
	'f = 7 + 2l is the answer as the "l" stands for long, which can also be capitalised to "L".',
	 'this is a comment');

INSERT INTO Questions (assessmentid,
	question, answer, check1, check2, check3, feedback, comment) VALUES ( 1,
	'Given a string p = "Python", which code below is incorrect?', 'p[1] = "p"',
	'print p[0]', 'print p.strip() ', 'print p.upper() ', 
	'In python strings are immutable, thus they cannot be altered. However, they can be used to create new strings',
	 'this is a comment');

INSERT INTO Assessments (name,content,type) VALUES  (
            'Python Exercise 1','here some content','formative');

INSERT INTO Assessments (name,content,type) VALUES  (
            'Java Exercise 1','here some content','formative');