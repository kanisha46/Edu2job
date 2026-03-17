"""
quiz.py – API for fetching mock test questions and submitting scores.
"""

from flask import Blueprint, jsonify, request, g
from auth import token_required
from database import update_user, find_user_by_email

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

JAVA_QUESTIONS = [
    {"id": 1, "q": "Which of these is not a primitive data type?", "options": ["int", "char", "String", "boolean"], "ans": "String"},
    {"id": 2, "q": "What is the size of float variable in Java?", "options": ["8 bit", "16 bit", "32 bit", "64 bit"], "ans": "32 bit"},
    {"id": 3, "q": "Which keyword is used to create a subclass in Java?", "options": ["extends", "implements", "inherits", "sub"], "ans": "extends"},
    {"id": 4, "q": "JVM stands for?", "options": ["Java Virtual Machine", "Java Variable Machine", "Joint Virtual Module", "None"], "ans": "Java Virtual Machine"},
    {"id": 5, "q": "Which of these is used to handle exceptions?", "options": ["try-catch", "if-else", "for-loop", "switch"], "ans": "try-catch"},
    {"id": 6, "q": "Default value of an integer variable in Java?", "options": ["0", "1", "null", "undefined"], "ans": "0"},
    {"id": 7, "q": "Which package contains the Scanner class?", "options": ["java.lang", "java.util", "java.io", "java.net"], "ans": "java.util"},
    {"id": 8, "q": "Can we override a static method?", "options": ["Yes", "No", "Only in same package", "Sometimes"], "ans": "No"},
    {"id": 9, "q": "Which of these is a reserved keyword?", "options": ["volatile", "main", "system", "value"], "ans": "volatile"},
    {"id": 10, "q": "Which method is the entry point of a Java program?", "options": ["start()", "main()", "init()", "run()"], "ans": "main()"},
    {"id": 11, "q": "Which memory is used for object storage?", "options": ["Stack", "Heap", "Registers", "Queue"], "ans": "Heap"},
    {"id": 12, "q": "Inheritance is used for?", "options": ["Encapsulation", "Code Reusability", "Security", "Compilation"], "ans": "Code Reusability"},
    {"id": 13, "q": "Final keyword on a class means?", "options": ["Cannot be inherited", "Cannot be instantiated", "Cannot have methods", "None"], "ans": "Cannot be inherited"},
    {"id": 14, "q": "Constructor return type is?", "options": ["void", "int", "No return type", "Object"], "ans": "No return type"},
    {"id": 15, "q": "Is Java platform independent?", "options": ["Yes", "No", "Partially", "Only on Windows"], "ans": "Yes"}
]

DSA_QUESTIONS = [
    {"id": 1, "q": "LIFO stands for?", "options": ["Last In First Out", "Lead In Fast Out", "Last In Final Out", "None"], "ans": "Last In First Out"},
    {"id": 2, "q": "Which data structure uses LIFO?", "options": ["Queue", "Stack", "Array", "Linked List"], "ans": "Stack"},
    {"id": 3, "q": "Which data structure uses FIFO?", "options": ["Stack", "Queue", "Tree", "Graph"], "ans": "Queue"},
    {"id": 4, "q": "Time complexity of searching in a Hash Table (average)?", "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"], "ans": "O(1)"},
    {"id": 5, "q": "A tree with no nodes is called?", "options": ["Empty Tree", "Null Tree", "Zero Tree", "Rootless"], "ans": "Null Tree"},
    {"id": 6, "q": "Which sort has O(n log n) average complexity?", "options": ["Bubble Sort", "Merge Sort", "Selection Sort", "Insertion Sort"], "ans": "Merge Sort"},
    {"id": 7, "q": "In a linked list, each node contains?", "options": ["Data", "Link", "Data & Link", "Address"], "ans": "Data & Link"},
    {"id": 8, "q": "Binary search works on?", "options": ["Sorted Array", "Unsorted Array", "Linked List", "Graph"], "ans": "Sorted Array"},
    {"id": 9, "q": "A graph with no cycles is called?", "options": ["Tree", "Path", "Acyclic Graph", "Linear Graph"], "ans": "Acyclic Graph"},
    {"id": 10, "q": "Full form of BST?", "options": ["Binary Search Tree", "Binary Selection Tool", "Basic Search Tree", "None"], "ans": "Binary Search Tree"},
    {"id": 11, "q": "Which is a linear data structure?", "options": ["Tree", "Graph", "Array", "BST"], "ans": "Array"},
    {"id": 12, "q": "Postfix expression for A+B?", "options": ["+AB", "AB+", "A+B", "BA+"], "ans": "AB+"},
    {"id": 13, "q": "Adding element to a stack is?", "options": ["Pop", "Push", "Enqueue", "Dequeue"], "ans": "Push"},
    {"id": 14, "q": "The height of a root node is?", "options": ["0", "1", "Height of tree", "-1"], "ans": "0"},
    {"id": 15, "q": "BFS uses which data structure?", "options": ["Stack", "Queue", "Tree", "Array"], "ans": "Queue"}
]

@quiz_bp.route("/<subject>", methods=["GET"])
@token_required
def get_quiz(subject):
    if subject.lower() == "java":
        return jsonify({"subject": "Java", "questions": JAVA_QUESTIONS}), 200
    elif subject.lower() == "dsa":
        return jsonify({"subject": "Data Structures", "questions": DSA_QUESTIONS}), 200
    else:
        return jsonify({"error": "Invalid subject"}), 404

@quiz_bp.route("/submit", methods=["POST"])
@token_required
def submit_quiz():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    score = data.get("score")
    subject = data.get("subject")
    date = data.get("date")

    if score is None or not subject:
        return jsonify({"error": "Missing score or subject"}), 400

    user = find_user_by_email(g.current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Append score to user's scores list
    scores = user.get("scores", [])
    scores.append({"subject": subject, "score": score, "date": date})
    
    update_user(g.current_user_email, {"scores": scores})

    return jsonify({"message": "Score saved successfully"}), 201

@quiz_bp.route("/scores", methods=["GET"])
@token_required
def get_scores():
    user = find_user_by_email(g.current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({"scores": user.get("scores", [])}), 200
