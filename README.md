# Matchmaker program

This program takes its input in the form of two files named "mentors.csv" and 
"mentees.csv", which must be adjacent to the match.py file. 

Within the "output" directory, there are several sub-directories: 

* mentor: This contains the standard report output
* interest: This is used for debugging (are there nulls?)
* oddball/primary: These are mostly for fun. They may have some useful application (like picking orientation day groups)

If running this program on Cloud9: right-click on the "output" folder and choose
"download" to download a compressed file containing all output html.

Jinja2 templates used for generating the html output are contained within the
"templates" directory.

To run this locally, install our dependencies with the command:

    pip install -r requirements.txt

# Technical notes

To anyone who wishes to modify this code:
I wish you the best of luck. You'll probably need it.

This program was built on top of a similar script, which leaves it with some weird
issues, unused code, commented-out features, and other interesting easter eggs.
Commenting will alternate between ok and sketchy.

It was written with the intent that nobody will need to look under the hood again,
but if worst comes to worst, here's some rough pointers:

* Brush up on your python, SQLite, HTML, CSS, and jinja2 templating. You'll need it all for anything really fancy.
* The code is executed relatively linearly and straight-forwardly, just start at the bottom function call.
* All the magic happens in "master\_query" and "parse\_main\_query"

If you really need help, try emailing the developer (class of '18!) at alexander.e.neuwirth@kmlhs.org
(I can't promise I'll be much help, but I'd certainly give it a shot if possible)

Otherwise, track down a mildly eccentric software dev by the name of Matt Hughes.
Tell him Xander sent you in a README file.
He might be helpful. He might also rewrite the whole thing in C++.
