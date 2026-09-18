print()
print("===============================")
print("     SMART STUDY PLANNER       ")
print("================================")

name = input("What is your name? ")
time = time = input("How many minutes do you have for studying today? ")

while not time.isdigit() or int(time) <= 0:
    print("Please enter a valid number greater than 0.")
    time = input("How many minutes do you have for studying today? ")

print("WELCOME!!",name)
print("Let's start your study plan now!!")
if int(time) < 60:
    print("You have less than 1 hour.")
    print("Let's make a short study plan.")
else:
    print("You have 1 hour or more.")
    print("Let's make a detailed study plan.")

mood = input("How are you feeling today? (good/tired/stressed) ").lower()

if mood == "good":
    print("Great! You can focus on difficult subjects today.")
elif mood == "tired":
    print("You seem tired. Let's keep today's plan light.")
elif mood == "stressed":
    print("You seem stressed. Let's start with an easy subject.")
else:
    print("I don't recognize that mood, so we'll make a normal study plan.")

subject1 = input("Enter your first subject: ").strip()
subject2 = input("Enter your second subject: ").strip()
subject3 = input("Enter your third subject: ").strip()

print("Your subjects are:")
print(subject1)
print(subject2)
print(subject3)

difficulty1 = input("How difficult is " + subject1 + "? (hard/medium/easy) ").lower()
difficulty2 = input("How difficult is " + subject2 + "? (hard/medium/easy) ").lower()
difficulty3 = input("How difficult is " + subject3 + "? (hard/medium/easy) ").lower()

print(" ")
print("===== SUBJECT DIFFICULTY =====")

print(subject1, ":", difficulty1)
print(subject2, ":", difficulty2)
print(subject3, ":", difficulty3)

if difficulty1 == "hard":
    weight1 = 3
elif difficulty1 == "medium":
    weight1 = 2
else:
    weight1 = 1

if difficulty2 == "hard":
    weight2 = 3
elif difficulty2 == "medium":
    weight2 = 2
else:
    weight2 = 1

if difficulty3 == "hard":
    weight3 = 3
elif difficulty3 == "medium":
    weight3 = 2
else:
    weight3 = 1
total_weight = weight1 + weight2 + weight3

if int(time) > 60:
    study_time = int(time) - 10
else:
    study_time = int(time)

time1 = int(study_time * weight1 / total_weight)
time2 = int(study_time * weight2 / total_weight)
time3 = int(study_time * weight3 / total_weight)

remaining_time = study_time - (time1 + time2 + time3)
time3 = time3 + remaining_time
print(" ")
print("===============================")
print("       YOUR STUDY PLAN")
print("===============================")

print(subject1, "→", time1, "minutes")
print(subject2, "→", time2, "minutes")
print(subject3, "→", time3, "minutes")

print("-------------------------------")
print("Total study time:", time1 + time2 + time3, "minutes")
print("===============================")
if int(time) > 60:
    print(" ")
    print("Take a 10-minute break after studying.")
else:
    print(" ")
    print("You can complete this short study session without a planned break.")
    print(" ")
print("===== STUDY ORDER =====")

if difficulty1 == "hard":
    print("1.", subject1)
    print("2.", subject2)
    print("3.", subject3)

elif difficulty2 == "hard":
    print("1.", subject2)
    print("2.", subject1)
    print("3.", subject3)

else:
    print("1.", subject3)
    print("2.", subject1)
    print("3.", subject2)
    print(" ")
print("===== TODAY'S TIMETABLE =====")

if difficulty1 == "hard":
    first_subject = subject1
    first_time = time1
    second_subject = subject2
    second_time = time2
    third_subject = subject3
    third_time = time3

elif difficulty2 == "hard":
    first_subject = subject2
    first_time = time2
    second_subject = subject1
    second_time = time1
    third_subject = subject3
    third_time = time3

else:
    first_subject = subject3
    first_time = time3
    second_subject = subject1
    second_time = time1
    third_subject = subject2
    third_time = time2
start1 = 0
end1 = first_time

start2 = end1
end2 = start2 + second_time

if int(time) > 60:
    break_start = end2
    break_end = break_start + 10
    start3 = break_end
else:
    start3 = end2

end3 = start3 + third_time
print("1.", first_subject, "→", start1, "-", end1, "minutes")
print("2.", second_subject, "→", start2, "-", end2, "minutes")

if int(time) > 60:
    print("☕ BREAK →", break_start, "-", break_end, "minutes")

print("3.", third_subject, "→", start3, "-", end3, "minutes")
print(" ")
print("===== STUDY SESSION READY =====")
print("Good luck with your studies,", name + "!")
print("Stay focused and make the most of your time.")
