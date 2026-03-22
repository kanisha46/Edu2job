"""
quiz_engine.py – Department-based interview prep quiz system.

Maps branches to subjects and provides MCQ question banks.
Separate from the original quiz.py to maintain backward compatibility.
"""

import logging
from flask import Blueprint, request, jsonify, g
from auth import token_required
from database import find_user_by_email, update_user

logger = logging.getLogger(__name__)

quiz_engine_bp = Blueprint("quiz_engine", __name__, url_prefix="/quiz-engine")

# ---------------------------------------------------------------------------
# Branch → Subjects mapping
# ---------------------------------------------------------------------------
BRANCH_SUBJECTS = {
    "Computer Science": [
        {"key": "java", "name": "Java Programming", "icon": "code", "desc": "Core Java, OOP, JVM internals"},
        {"key": "dsa", "name": "Data Structures & Algorithms", "icon": "account_tree", "desc": "Arrays, Trees, Graphs, Sorting"},
        {"key": "dbms", "name": "Database Management", "icon": "storage", "desc": "SQL, Normalization, Transactions"},
        {"key": "os", "name": "Operating Systems", "icon": "memory", "desc": "Processes, Scheduling, Memory"},
        {"key": "cn", "name": "Computer Networks", "icon": "lan", "desc": "TCP/IP, OSI Model, Routing"},
    ],
    "IT": [
        {"key": "java", "name": "Java Programming", "icon": "code", "desc": "Core Java, OOP, JVM internals"},
        {"key": "dsa", "name": "Data Structures & Algorithms", "icon": "account_tree", "desc": "Arrays, Trees, Graphs, Sorting"},
        {"key": "dbms", "name": "Database Management", "icon": "storage", "desc": "SQL, Normalization, Transactions"},
        {"key": "cn", "name": "Computer Networks", "icon": "lan", "desc": "TCP/IP, OSI Model, Routing"},
        {"key": "webtech", "name": "Web Technologies", "icon": "web", "desc": "HTML, CSS, JavaScript, HTTP"},
    ],
    "ECE": [
        {"key": "cn", "name": "Computer Networks", "icon": "lan", "desc": "TCP/IP, OSI Model, Routing"},
        {"key": "signals", "name": "Signals & Systems", "icon": "graphic_eq", "desc": "Fourier, Laplace, Z-Transform"},
        {"key": "embedded", "name": "Embedded Systems", "icon": "developer_board", "desc": "Microcontrollers, RTOS, I/O"},
        {"key": "digital", "name": "Digital Electronics", "icon": "memory", "desc": "Logic Gates, Flip-Flops, Counters"},
    ],
    "EE": [
        {"key": "circuits", "name": "Circuit Analysis", "icon": "electric_bolt", "desc": "KVL, KCL, Thevenin, Norton"},
        {"key": "power", "name": "Power Systems", "icon": "bolt", "desc": "Generation, Transmission, Distribution"},
        {"key": "control", "name": "Control Systems", "icon": "tune", "desc": "Transfer Functions, Stability, PID"},
    ],
    "ME": [
        {"key": "thermo", "name": "Thermodynamics", "icon": "thermostat", "desc": "Laws, Cycles, Entropy"},
        {"key": "fluids", "name": "Fluid Mechanics", "icon": "water_drop", "desc": "Bernoulli, Viscosity, Flow"},
        {"key": "manufacturing", "name": "Manufacturing", "icon": "precision_manufacturing", "desc": "Casting, Machining, Welding"},
    ],
    "Civil": [
        {"key": "structural", "name": "Structural Analysis", "icon": "domain", "desc": "Beams, Trusses, Columns"},
        {"key": "geotech", "name": "Geotechnical Engg", "icon": "landscape", "desc": "Soil Mechanics, Foundations"},
        {"key": "surveying", "name": "Surveying", "icon": "straighten", "desc": "Leveling, Contouring, GPS"},
    ],
    "AI/ML": [
        {"key": "java", "name": "Java Programming", "icon": "code", "desc": "Core Java, OOP, JVM internals"},
        {"key": "dsa", "name": "Data Structures & Algorithms", "icon": "account_tree", "desc": "Arrays, Trees, Graphs, Sorting"},
        {"key": "dbms", "name": "Database Management", "icon": "storage", "desc": "SQL, Normalization, Transactions"},
        {"key": "os", "name": "Operating Systems", "icon": "memory", "desc": "Processes, Scheduling, Memory"},
        {"key": "cn", "name": "Computer Networks", "icon": "lan", "desc": "TCP/IP, OSI Model, Routing"},
    ],
    "Data Science": [
        {"key": "java", "name": "Java Programming", "icon": "code", "desc": "Core Java, OOP, JVM internals"},
        {"key": "dsa", "name": "Data Structures & Algorithms", "icon": "account_tree", "desc": "Arrays, Trees, Graphs, Sorting"},
        {"key": "dbms", "name": "Database Management", "icon": "storage", "desc": "SQL, Normalization, Transactions"},
        {"key": "os", "name": "Operating Systems", "icon": "memory", "desc": "Processes, Scheduling, Memory"},
        {"key": "cn", "name": "Computer Networks", "icon": "lan", "desc": "TCP/IP, OSI Model, Routing"},
    ],
}

# ---------------------------------------------------------------------------
# Question Bank – 15 MCQs per subject
# ---------------------------------------------------------------------------
QUESTION_BANK = {
    "java": [
        {"id":1,"q":"Which is not a primitive type?","options":["int","char","String","boolean"],"ans":"String"},
        {"id":2,"q":"Size of float in Java?","options":["8 bit","16 bit","32 bit","64 bit"],"ans":"32 bit"},
        {"id":3,"q":"Keyword for subclass?","options":["extends","implements","inherits","sub"],"ans":"extends"},
        {"id":4,"q":"JVM stands for?","options":["Java Virtual Machine","Java Variable Machine","Joint Virtual Module","None"],"ans":"Java Virtual Machine"},
        {"id":5,"q":"Exception handling uses?","options":["try-catch","if-else","for-loop","switch"],"ans":"try-catch"},
        {"id":6,"q":"Default int value?","options":["0","1","null","undefined"],"ans":"0"},
        {"id":7,"q":"Scanner class package?","options":["java.lang","java.util","java.io","java.net"],"ans":"java.util"},
        {"id":8,"q":"Can static methods be overridden?","options":["Yes","No","Only in same package","Sometimes"],"ans":"No"},
        {"id":9,"q":"Which is a reserved keyword?","options":["volatile","main","system","value"],"ans":"volatile"},
        {"id":10,"q":"Entry point method?","options":["start()","main()","init()","run()"],"ans":"main()"},
        {"id":11,"q":"Object storage memory?","options":["Stack","Heap","Registers","Queue"],"ans":"Heap"},
        {"id":12,"q":"Inheritance purpose?","options":["Encapsulation","Code Reusability","Security","Compilation"],"ans":"Code Reusability"},
        {"id":13,"q":"Final class means?","options":["Cannot be inherited","Cannot be instantiated","Cannot have methods","None"],"ans":"Cannot be inherited"},
        {"id":14,"q":"Constructor return type?","options":["void","int","No return type","Object"],"ans":"No return type"},
        {"id":15,"q":"Is Java platform independent?","options":["Yes","No","Partially","Only on Windows"],"ans":"Yes"},
    ],
    "dsa": [
        {"id":1,"q":"LIFO stands for?","options":["Last In First Out","Lead In Fast Out","Last In Final Out","None"],"ans":"Last In First Out"},
        {"id":2,"q":"Which uses LIFO?","options":["Queue","Stack","Array","Linked List"],"ans":"Stack"},
        {"id":3,"q":"Which uses FIFO?","options":["Stack","Queue","Tree","Graph"],"ans":"Queue"},
        {"id":4,"q":"Hash Table search avg?","options":["O(1)","O(n)","O(log n)","O(n^2)"],"ans":"O(1)"},
        {"id":5,"q":"Tree with no nodes?","options":["Empty Tree","Null Tree","Zero Tree","Rootless"],"ans":"Null Tree"},
        {"id":6,"q":"O(n log n) avg sort?","options":["Bubble","Merge","Selection","Insertion"],"ans":"Merge"},
        {"id":7,"q":"Linked list node has?","options":["Data","Link","Data & Link","Address"],"ans":"Data & Link"},
        {"id":8,"q":"Binary search needs?","options":["Sorted Array","Unsorted Array","Linked List","Graph"],"ans":"Sorted Array"},
        {"id":9,"q":"Graph with no cycles?","options":["Tree","Path","Acyclic Graph","Linear Graph"],"ans":"Acyclic Graph"},
        {"id":10,"q":"BST full form?","options":["Binary Search Tree","Binary Selection Tool","Basic Search Tree","None"],"ans":"Binary Search Tree"},
        {"id":11,"q":"Which is linear?","options":["Tree","Graph","Array","BST"],"ans":"Array"},
        {"id":12,"q":"Postfix of A+B?","options":["+AB","AB+","A+B","BA+"],"ans":"AB+"},
        {"id":13,"q":"Adding to stack?","options":["Pop","Push","Enqueue","Dequeue"],"ans":"Push"},
        {"id":14,"q":"Root node height?","options":["0","1","Height of tree","-1"],"ans":"0"},
        {"id":15,"q":"BFS uses?","options":["Stack","Queue","Tree","Array"],"ans":"Queue"},
    ],
    "dbms": [
        {"id":1,"q":"ACID stands for?","options":["Atomicity Consistency Isolation Durability","Add Change Insert Delete","None","All Correct"],"ans":"Atomicity Consistency Isolation Durability"},
        {"id":2,"q":"Primary key allows NULL?","options":["Yes","No","Sometimes","Depends"],"ans":"No"},
        {"id":3,"q":"Which is a DDL command?","options":["SELECT","INSERT","CREATE","UPDATE"],"ans":"CREATE"},
        {"id":4,"q":"Normal form removing partial dependency?","options":["1NF","2NF","3NF","BCNF"],"ans":"2NF"},
        {"id":5,"q":"Foreign key ensures?","options":["Referential Integrity","Data Speed","Indexing","Backup"],"ans":"Referential Integrity"},
        {"id":6,"q":"JOIN combines?","options":["Rows from two tables","Columns only","Indexes","Triggers"],"ans":"Rows from two tables"},
        {"id":7,"q":"Which is a DML command?","options":["DROP","CREATE","ALTER","INSERT"],"ans":"INSERT"},
        {"id":8,"q":"Deadlock involves?","options":["Circular wait","Fast queries","Indexing","Backup"],"ans":"Circular wait"},
        {"id":9,"q":"View is a?","options":["Virtual table","Physical table","Stored procedure","Trigger"],"ans":"Virtual table"},
        {"id":10,"q":"HAVING clause filters?","options":["Groups","Rows","Columns","Tables"],"ans":"Groups"},
        {"id":11,"q":"AUTO_INCREMENT is used for?","options":["Auto-generating IDs","Sorting","Joining","Deleting"],"ans":"Auto-generating IDs"},
        {"id":12,"q":"Which is not an aggregate function?","options":["SUM","AVG","CONCAT","COUNT"],"ans":"CONCAT"},
        {"id":13,"q":"Schema defines?","options":["Structure of database","Data values","Queries","Users"],"ans":"Structure of database"},
        {"id":14,"q":"Transaction isolation prevents?","options":["Dirty reads","Fast writes","Backups","Indexing"],"ans":"Dirty reads"},
        {"id":15,"q":"B+ Tree is used in?","options":["Indexing","Sorting","Hashing","Backup"],"ans":"Indexing"},
    ],
    "os": [
        {"id":1,"q":"OS stands for?","options":["Operating System","Open Software","Output System","None"],"ans":"Operating System"},
        {"id":2,"q":"CPU scheduling: FCFS means?","options":["First Come First Served","Fast CPU First System","None","File Control"],"ans":"First Come First Served"},
        {"id":3,"q":"Deadlock condition count?","options":["2","3","4","5"],"ans":"4"},
        {"id":4,"q":"Virtual memory uses?","options":["Disk as RAM extension","More CPU","Faster GPU","None"],"ans":"Disk as RAM extension"},
        {"id":5,"q":"Semaphore is used for?","options":["Synchronization","Scheduling","Memory","I/O"],"ans":"Synchronization"},
        {"id":6,"q":"Page fault means?","options":["Page not in memory","Page corrupted","Page deleted","None"],"ans":"Page not in memory"},
        {"id":7,"q":"Shortest Job First is?","options":["Preemptive","Non-preemptive","Both possible","Neither"],"ans":"Both possible"},
        {"id":8,"q":"Thrashing means?","options":["Excessive paging","Fast processing","Memory leak","None"],"ans":"Excessive paging"},
        {"id":9,"q":"Process states include?","options":["Ready, Running, Waiting","Only Running","Start, End","None"],"ans":"Ready, Running, Waiting"},
        {"id":10,"q":"Kernel is?","options":["Core of OS","Application","Browser","Compiler"],"ans":"Core of OS"},
        {"id":11,"q":"Mutex allows?","options":["One thread at a time","Multiple threads","No threads","None"],"ans":"One thread at a time"},
        {"id":12,"q":"Round Robin uses?","options":["Time quantum","Priority","Burst time","Arrival time"],"ans":"Time quantum"},
        {"id":13,"q":"Fork() creates?","options":["Child process","Thread","File","Socket"],"ans":"Child process"},
        {"id":14,"q":"Paging avoids?","options":["External fragmentation","Internal fragmentation","Both","Neither"],"ans":"External fragmentation"},
        {"id":15,"q":"Spooling is used for?","options":["I/O management","CPU scheduling","Memory","Security"],"ans":"I/O management"},
    ],
    "cn": [
        {"id":1,"q":"OSI model layers?","options":["5","6","7","8"],"ans":"7"},
        {"id":2,"q":"TCP is?","options":["Connection-oriented","Connectionless","Both","Neither"],"ans":"Connection-oriented"},
        {"id":3,"q":"IP address version 4 bits?","options":["16","32","64","128"],"ans":"32"},
        {"id":4,"q":"HTTP port number?","options":["21","22","80","443"],"ans":"80"},
        {"id":5,"q":"DNS resolves?","options":["Domain to IP","IP to MAC","Port to IP","None"],"ans":"Domain to IP"},
        {"id":6,"q":"Which layer handles routing?","options":["Physical","Data Link","Network","Transport"],"ans":"Network"},
        {"id":7,"q":"UDP is?","options":["Connection-oriented","Connectionless","Both","Neither"],"ans":"Connectionless"},
        {"id":8,"q":"Subnet mask purpose?","options":["Divide network","Encrypt data","Compress data","None"],"ans":"Divide network"},
        {"id":9,"q":"ARP resolves?","options":["IP to MAC","MAC to IP","Domain to IP","None"],"ans":"IP to MAC"},
        {"id":10,"q":"FTP port?","options":["20/21","22","80","443"],"ans":"20/21"},
        {"id":11,"q":"Which topology has central node?","options":["Bus","Ring","Star","Mesh"],"ans":"Star"},
        {"id":12,"q":"SMTP is for?","options":["Email sending","File transfer","Web browsing","DNS"],"ans":"Email sending"},
        {"id":13,"q":"Router works at?","options":["Layer 1","Layer 2","Layer 3","Layer 4"],"ans":"Layer 3"},
        {"id":14,"q":"Firewall purpose?","options":["Network security","Speed boost","Data storage","None"],"ans":"Network security"},
        {"id":15,"q":"HTTPS port?","options":["21","22","80","443"],"ans":"443"},
    ],
    "webtech": [
        {"id":1,"q":"HTML stands for?","options":["HyperText Markup Language","High Tech ML","None","Hyper Transfer ML"],"ans":"HyperText Markup Language"},
        {"id":2,"q":"CSS is for?","options":["Styling","Logic","Database","Server"],"ans":"Styling"},
        {"id":3,"q":"JavaScript runs in?","options":["Browser","Database","OS kernel","None"],"ans":"Browser"},
        {"id":4,"q":"HTTP method for fetching?","options":["GET","POST","PUT","DELETE"],"ans":"GET"},
        {"id":5,"q":"JSON stands for?","options":["JavaScript Object Notation","Java System Object","None","JS Online"],"ans":"JavaScript Object Notation"},
        {"id":6,"q":"Which is a CSS framework?","options":["Bootstrap","React","Node","Django"],"ans":"Bootstrap"},
        {"id":7,"q":"DOM stands for?","options":["Document Object Model","Data Output Module","None","Digital Object"],"ans":"Document Object Model"},
        {"id":8,"q":"REST API uses?","options":["HTTP methods","FTP","SMTP","TCP only"],"ans":"HTTP methods"},
        {"id":9,"q":"Cookie stores data on?","options":["Client side","Server side","Database","Cloud"],"ans":"Client side"},
        {"id":10,"q":"Which tag for links?","options":["<a>","<link>","<href>","<url>"],"ans":"<a>"},
        {"id":11,"q":"PHP is?","options":["Server-side","Client-side","Database","OS"],"ans":"Server-side"},
        {"id":12,"q":"AJAX allows?","options":["Async requests","Styling","Database","Routing"],"ans":"Async requests"},
        {"id":13,"q":"Responsive design uses?","options":["Media queries","Threads","Sockets","None"],"ans":"Media queries"},
        {"id":14,"q":"npm is for?","options":["Package management","Styling","Database","Testing"],"ans":"Package management"},
        {"id":15,"q":"SPA stands for?","options":["Single Page Application","Server Page App","None","Simple Page"],"ans":"Single Page Application"},
    ],
    "signals": [
        {"id":1,"q":"Fourier Transform converts?","options":["Time to Frequency","Frequency to Time","Both","Neither"],"ans":"Time to Frequency"},
        {"id":2,"q":"Laplace variable is?","options":["s","z","f","t"],"ans":"s"},
        {"id":3,"q":"Unit step function value at t>0?","options":["0","1","-1","Infinity"],"ans":"1"},
        {"id":4,"q":"Convolution is?","options":["Integral operation","Derivative","Sum","Product"],"ans":"Integral operation"},
        {"id":5,"q":"Z-Transform is for?","options":["Discrete signals","Continuous","Both","Neither"],"ans":"Discrete signals"},
        {"id":6,"q":"Nyquist rate is?","options":["2 × max frequency","Max frequency","Half frequency","None"],"ans":"2 × max frequency"},
        {"id":7,"q":"LTI stands for?","options":["Linear Time Invariant","Low Transfer Input","None","Linear Total"],"ans":"Linear Time Invariant"},
        {"id":8,"q":"Impulse response symbol?","options":["h(t)","x(t)","y(t)","u(t)"],"ans":"h(t)"},
        {"id":9,"q":"Causal system depends on?","options":["Past & present","Future","Both","Neither"],"ans":"Past & present"},
        {"id":10,"q":"Energy signal has?","options":["Finite energy","Infinite energy","Zero energy","None"],"ans":"Finite energy"},
        {"id":11,"q":"Sampling theorem by?","options":["Nyquist","Fourier","Laplace","Newton"],"ans":"Nyquist"},
        {"id":12,"q":"ROC in Z-transform is?","options":["Region of Convergence","Rate of Change","Range","None"],"ans":"Region of Convergence"},
        {"id":13,"q":"Even signal condition?","options":["x(t) = x(-t)","x(t) = -x(-t)","x(t) = 0","None"],"ans":"x(t) = x(-t)"},
        {"id":14,"q":"System stability needs?","options":["Bounded output","Infinite output","No output","None"],"ans":"Bounded output"},
        {"id":15,"q":"DFT stands for?","options":["Discrete Fourier Transform","Digital Frequency","None","Data Filter"],"ans":"Discrete Fourier Transform"},
    ],
    "embedded": [
        {"id":1,"q":"Microcontroller has?","options":["CPU, Memory, I/O","Only CPU","Only Memory","None"],"ans":"CPU, Memory, I/O"},
        {"id":2,"q":"RTOS stands for?","options":["Real Time Operating System","Random Transfer OS","None","Rapid"],"ans":"Real Time Operating System"},
        {"id":3,"q":"GPIO stands for?","options":["General Purpose I/O","Global Pin Output","None","Generic Port"],"ans":"General Purpose I/O"},
        {"id":4,"q":"ADC converts?","options":["Analog to Digital","Digital to Analog","Both","Neither"],"ans":"Analog to Digital"},
        {"id":5,"q":"I2C is?","options":["Serial protocol","Parallel","Wireless","None"],"ans":"Serial protocol"},
        {"id":6,"q":"PWM is used for?","options":["Motor speed control","Memory","Display","None"],"ans":"Motor speed control"},
        {"id":7,"q":"ARM is a?","options":["Processor architecture","Language","OS","Protocol"],"ans":"Processor architecture"},
        {"id":8,"q":"Watchdog timer prevents?","options":["System hang","Memory leak","Hacking","None"],"ans":"System hang"},
        {"id":9,"q":"UART is?","options":["Async serial","Sync serial","Parallel","None"],"ans":"Async serial"},
        {"id":10,"q":"Flash memory is?","options":["Non-volatile","Volatile","Both","Neither"],"ans":"Non-volatile"},
        {"id":11,"q":"SPI uses how many wires?","options":["2","3","4","5"],"ans":"4"},
        {"id":12,"q":"Interrupt is?","options":["Signal to CPU","Memory error","I/O block","None"],"ans":"Signal to CPU"},
        {"id":13,"q":"Bootloader does?","options":["Loads OS","Compiles code","Tests memory","None"],"ans":"Loads OS"},
        {"id":14,"q":"DMA stands for?","options":["Direct Memory Access","Data Memory Array","None","Digital"],"ans":"Direct Memory Access"},
        {"id":15,"q":"Timer in MCU is for?","options":["Time measurement","Storage","Display","None"],"ans":"Time measurement"},
    ],
    "digital": [
        {"id":1,"q":"AND gate: 1 AND 0 =?","options":["0","1","X","None"],"ans":"0"},
        {"id":2,"q":"OR gate: 0 OR 1 =?","options":["0","1","X","None"],"ans":"1"},
        {"id":3,"q":"NOT gate inverts?","options":["Yes","No","Sometimes","Never"],"ans":"Yes"},
        {"id":4,"q":"Flip-flop stores?","options":["1 bit","1 byte","1 word","None"],"ans":"1 bit"},
        {"id":5,"q":"Full adder inputs?","options":["2","3","4","1"],"ans":"3"},
        {"id":6,"q":"K-Map simplifies?","options":["Boolean expressions","Circuits","Signals","None"],"ans":"Boolean expressions"},
        {"id":7,"q":"Binary of 10 decimal?","options":["1010","1100","1001","1110"],"ans":"1010"},
        {"id":8,"q":"Multiplexer selects?","options":["One of many inputs","Many outputs","Both","None"],"ans":"One of many inputs"},
        {"id":9,"q":"Counter counts?","options":["Clock pulses","Voltage","Current","None"],"ans":"Clock pulses"},
        {"id":10,"q":"NAND is universal because?","options":["Can make any gate","Fastest","Cheapest","None"],"ans":"Can make any gate"},
        {"id":11,"q":"Decoder converts?","options":["Binary to output lines","Analog to Digital","None","Both"],"ans":"Binary to output lines"},
        {"id":12,"q":"SR latch has?","options":["Set and Reset","Shift and Rotate","None","Start and Run"],"ans":"Set and Reset"},
        {"id":13,"q":"XOR: 1 XOR 1 =?","options":["0","1","X","None"],"ans":"0"},
        {"id":14,"q":"Register stores?","options":["Multiple bits","Single bit","Analog","None"],"ans":"Multiple bits"},
        {"id":15,"q":"De Morgan's law relates?","options":["AND, OR, NOT","Only AND","Only OR","None"],"ans":"AND, OR, NOT"},
    ],
    "circuits": [
        {"id":1,"q":"KVL is about?","options":["Voltage in a loop","Current at node","Power","None"],"ans":"Voltage in a loop"},
        {"id":2,"q":"KCL is about?","options":["Current at a node","Voltage in loop","Resistance","None"],"ans":"Current at a node"},
        {"id":3,"q":"Thevenin equivalent has?","options":["Voltage source + series R","Current source","Both","None"],"ans":"Voltage source + series R"},
        {"id":4,"q":"Ohm's law: V =?","options":["IR","I/R","R/I","None"],"ans":"IR"},
        {"id":5,"q":"Capacitor stores?","options":["Charge","Current","Resistance","None"],"ans":"Charge"},
        {"id":6,"q":"Inductor opposes?","options":["Change in current","Change in voltage","Both","None"],"ans":"Change in current"},
        {"id":7,"q":"Resonance occurs when?","options":["XL = XC","R = 0","V = 0","None"],"ans":"XL = XC"},
        {"id":8,"q":"Power factor range?","options":["0 to 1","-1 to 1","0 to infinity","None"],"ans":"0 to 1"},
        {"id":9,"q":"Series R total?","options":["R1 + R2","R1 × R2","1/R1 + 1/R2","None"],"ans":"R1 + R2"},
        {"id":10,"q":"AC frequency unit?","options":["Hertz","Ohm","Watt","Volt"],"ans":"Hertz"},
        {"id":11,"q":"Impedance unit?","options":["Ohm","Farad","Henry","Watt"],"ans":"Ohm"},
        {"id":12,"q":"Norton has?","options":["Current source + parallel R","Voltage source","Both","None"],"ans":"Current source + parallel R"},
        {"id":13,"q":"Diode allows?","options":["One-way current","Two-way","No current","None"],"ans":"One-way current"},
        {"id":14,"q":"Transformer changes?","options":["Voltage level","Current frequency","Resistance","None"],"ans":"Voltage level"},
        {"id":15,"q":"RMS stands for?","options":["Root Mean Square","Rate Mean Sum","None","Real Mean"],"ans":"Root Mean Square"},
    ],
    "power": [
        {"id":1,"q":"Thermal power uses?","options":["Coal/Gas","Wind","Solar","Tidal"],"ans":"Coal/Gas"},
        {"id":2,"q":"Transmission voltage is?","options":["High","Low","Medium","Zero"],"ans":"High"},
        {"id":3,"q":"Distribution is?","options":["Low voltage to consumers","High voltage","Generation","None"],"ans":"Low voltage to consumers"},
        {"id":4,"q":"Power factor improvement uses?","options":["Capacitor bank","Resistor","Inductor only","None"],"ans":"Capacitor bank"},
        {"id":5,"q":"Per unit system simplifies?","options":["Calculations","Wiring","Safety","None"],"ans":"Calculations"},
        {"id":6,"q":"Load flow analysis finds?","options":["Voltage & power","Only current","Only resistance","None"],"ans":"Voltage & power"},
        {"id":7,"q":"Circuit breaker does?","options":["Interrupt fault current","Generate power","Store energy","None"],"ans":"Interrupt fault current"},
        {"id":8,"q":"Relay is for?","options":["Protection","Generation","Transmission","None"],"ans":"Protection"},
        {"id":9,"q":"Earthing purpose?","options":["Safety","Speed","Power factor","None"],"ans":"Safety"},
        {"id":10,"q":"HVDC stands for?","options":["High Voltage Direct Current","High Volt DC","None","Heavy Voltage"],"ans":"High Voltage Direct Current"},
        {"id":11,"q":"Generator converts?","options":["Mechanical to Electrical","Electrical to Mechanical","Heat to Light","None"],"ans":"Mechanical to Electrical"},
        {"id":12,"q":"Demand factor is?","options":["Max demand / Total load","Total / Max","Average / Max","None"],"ans":"Max demand / Total load"},
        {"id":13,"q":"Skin effect is in?","options":["AC conductors","DC conductors","Both","None"],"ans":"AC conductors"},
        {"id":14,"q":"Corona occurs at?","options":["High voltage","Low voltage","No voltage","None"],"ans":"High voltage"},
        {"id":15,"q":"Tariff is?","options":["Electricity pricing","Wiring","Generation","None"],"ans":"Electricity pricing"},
    ],
    "control": [
        {"id":1,"q":"Transfer function is?","options":["Output/Input in s-domain","Time response","Frequency","None"],"ans":"Output/Input in s-domain"},
        {"id":2,"q":"Open loop has?","options":["No feedback","Feedback","Both","None"],"ans":"No feedback"},
        {"id":3,"q":"Closed loop has?","options":["Feedback","No feedback","Both","None"],"ans":"Feedback"},
        {"id":4,"q":"PID stands for?","options":["Proportional Integral Derivative","Power Input Device","None","Phase"],"ans":"Proportional Integral Derivative"},
        {"id":5,"q":"Bode plot shows?","options":["Magnitude & Phase vs Frequency","Time response","Both","None"],"ans":"Magnitude & Phase vs Frequency"},
        {"id":6,"q":"Stable system poles are in?","options":["Left half of s-plane","Right half","Origin","None"],"ans":"Left half of s-plane"},
        {"id":7,"q":"Routh criterion checks?","options":["Stability","Speed","Gain","None"],"ans":"Stability"},
        {"id":8,"q":"Root locus plots?","options":["Pole locations vs gain","Zeros only","Frequency","None"],"ans":"Pole locations vs gain"},
        {"id":9,"q":"Gain margin is at?","options":["Phase crossover","Gain crossover","Origin","None"],"ans":"Phase crossover"},
        {"id":10,"q":"Step response shows?","options":["System behavior to step input","Frequency","Poles","None"],"ans":"System behavior to step input"},
        {"id":11,"q":"Time constant unit?","options":["Seconds","Hertz","Watts","None"],"ans":"Seconds"},
        {"id":12,"q":"Nyquist plot is?","options":["Polar plot of frequency response","Time plot","Root locus","None"],"ans":"Polar plot of frequency response"},
        {"id":13,"q":"Damping affects?","options":["Oscillations","Frequency","Gain","None"],"ans":"Oscillations"},
        {"id":14,"q":"Lag compensator adds?","options":["Phase lag","Phase lead","Both","None"],"ans":"Phase lag"},
        {"id":15,"q":"State space uses?","options":["Matrices","Single equation","Graph","None"],"ans":"Matrices"},
    ],
    "thermo": [
        {"id":1,"q":"First law is about?","options":["Energy conservation","Entropy","Enthalpy","None"],"ans":"Energy conservation"},
        {"id":2,"q":"Second law involves?","options":["Entropy","Energy","Mass","None"],"ans":"Entropy"},
        {"id":3,"q":"Carnot cycle has?","options":["Max efficiency","Min efficiency","Zero","None"],"ans":"Max efficiency"},
        {"id":4,"q":"Enthalpy = ?","options":["U + PV","U - PV","PV only","None"],"ans":"U + PV"},
        {"id":5,"q":"Isothermal means?","options":["Constant temperature","Constant pressure","Constant volume","None"],"ans":"Constant temperature"},
        {"id":6,"q":"Adiabatic means?","options":["No heat exchange","No work","No pressure","None"],"ans":"No heat exchange"},
        {"id":7,"q":"Specific heat at constant P?","options":["Cp","Cv","R","None"],"ans":"Cp"},
        {"id":8,"q":"Otto cycle is for?","options":["SI engines","CI engines","Turbines","None"],"ans":"SI engines"},
        {"id":9,"q":"Diesel cycle is for?","options":["CI engines","SI engines","Turbines","None"],"ans":"CI engines"},
        {"id":10,"q":"Zeroth law defines?","options":["Temperature","Pressure","Volume","None"],"ans":"Temperature"},
        {"id":11,"q":"Triple point of water?","options":["273.16 K","0 K","100 K","373 K"],"ans":"273.16 K"},
        {"id":12,"q":"Refrigerator COP formula?","options":["QL/W","QH/W","W/QL","None"],"ans":"QL/W"},
        {"id":13,"q":"Rankine cycle is for?","options":["Steam power plants","Gas turbines","IC engines","None"],"ans":"Steam power plants"},
        {"id":14,"q":"Entropy unit?","options":["J/K","W","Pa","None"],"ans":"J/K"},
        {"id":15,"q":"Third law: at 0 K?","options":["Entropy is zero","Energy is zero","Both","None"],"ans":"Entropy is zero"},
    ],
    "fluids": [
        {"id":1,"q":"Bernoulli's principle is about?","options":["Pressure & velocity","Temperature","Mass","None"],"ans":"Pressure & velocity"},
        {"id":2,"q":"Viscosity measures?","options":["Fluid resistance","Speed","Pressure","None"],"ans":"Fluid resistance"},
        {"id":3,"q":"Reynolds number predicts?","options":["Flow type","Pressure","Temperature","None"],"ans":"Flow type"},
        {"id":4,"q":"Laminar flow is?","options":["Smooth","Turbulent","Both","None"],"ans":"Smooth"},
        {"id":5,"q":"Pascal's law is about?","options":["Pressure transmission","Velocity","Mass","None"],"ans":"Pressure transmission"},
        {"id":6,"q":"Archimedes' principle involves?","options":["Buoyancy","Gravity","Friction","None"],"ans":"Buoyancy"},
        {"id":7,"q":"Continuity equation: A1V1 =?","options":["A2V2","A2/V2","P1V1","None"],"ans":"A2V2"},
        {"id":8,"q":"Stagnation pressure is?","options":["Static + Dynamic","Only Static","Only Dynamic","None"],"ans":"Static + Dynamic"},
        {"id":9,"q":"Mach number > 1 means?","options":["Supersonic","Subsonic","Sonic","None"],"ans":"Supersonic"},
        {"id":10,"q":"Venturi meter measures?","options":["Flow rate","Pressure only","Temperature","None"],"ans":"Flow rate"},
        {"id":11,"q":"Ideal fluid has?","options":["No viscosity","High viscosity","No density","None"],"ans":"No viscosity"},
        {"id":12,"q":"Cavitation is?","options":["Bubble formation","Solidification","Evaporation","None"],"ans":"Bubble formation"},
        {"id":13,"q":"Hydraulic press uses?","options":["Pascal's law","Bernoulli","Archimedes","None"],"ans":"Pascal's law"},
        {"id":14,"q":"Drag force opposes?","options":["Motion","Gravity","Buoyancy","None"],"ans":"Motion"},
        {"id":15,"q":"Turbulent flow Re > ?","options":["4000","2000","1000","500"],"ans":"4000"},
    ],
    "manufacturing": [
        {"id":1,"q":"Casting uses?","options":["Molten metal in mold","Cutting","Welding","None"],"ans":"Molten metal in mold"},
        {"id":2,"q":"Turning is done on?","options":["Lathe","Drill","Milling","Shaper"],"ans":"Lathe"},
        {"id":3,"q":"Welding joins by?","options":["Heat/Pressure","Adhesive","Bolts","None"],"ans":"Heat/Pressure"},
        {"id":4,"q":"CNC stands for?","options":["Computer Numerical Control","Central Numeric","None","Controlled"],"ans":"Computer Numerical Control"},
        {"id":5,"q":"Forging uses?","options":["Compressive force","Tensile","Shear","None"],"ans":"Compressive force"},
        {"id":6,"q":"Drilling creates?","options":["Holes","Flat surfaces","Threads","None"],"ans":"Holes"},
        {"id":7,"q":"Sheet metal forming includes?","options":["Bending","Casting","Welding","None"],"ans":"Bending"},
        {"id":8,"q":"Tolerance is?","options":["Permissible variation","Exact size","Error","None"],"ans":"Permissible variation"},
        {"id":9,"q":"Surface finish unit?","options":["Micron","Meter","Millimeter","None"],"ans":"Micron"},
        {"id":10,"q":"Extrusion pushes material through?","options":["Die","Mold","Furnace","None"],"ans":"Die"},
        {"id":11,"q":"Grinding is?","options":["Finishing process","Rough cutting","Casting","None"],"ans":"Finishing process"},
        {"id":12,"q":"Jig purpose?","options":["Guide cutting tool","Hold only","Measure","None"],"ans":"Guide cutting tool"},
        {"id":13,"q":"Heat treatment changes?","options":["Properties of metal","Shape","Size","None"],"ans":"Properties of metal"},
        {"id":14,"q":"Rolling reduces?","options":["Thickness","Length","Width","None"],"ans":"Thickness"},
        {"id":15,"q":"3D printing is?","options":["Additive manufacturing","Subtractive","Casting","None"],"ans":"Additive manufacturing"},
    ],
    "structural": [
        {"id":1,"q":"Beam supports load by?","options":["Bending","Tension only","Compression only","None"],"ans":"Bending"},
        {"id":2,"q":"Truss members carry?","options":["Axial forces","Bending","Torsion","None"],"ans":"Axial forces"},
        {"id":3,"q":"Moment of inertia unit?","options":["m^4","m^2","m^3","m"],"ans":"m^4"},
        {"id":4,"q":"Shear force diagram shows?","options":["Internal shear","External load","Deflection","None"],"ans":"Internal shear"},
        {"id":5,"q":"BMD stands for?","options":["Bending Moment Diagram","Basic Moment","None","Beam Model"],"ans":"Bending Moment Diagram"},
        {"id":6,"q":"Fixed beam has?","options":["Both ends fixed","One end free","Both free","None"],"ans":"Both ends fixed"},
        {"id":7,"q":"Cantilever has?","options":["One fixed, one free","Both fixed","Both free","None"],"ans":"One fixed, one free"},
        {"id":8,"q":"Young's modulus measures?","options":["Stiffness","Strength","Ductility","None"],"ans":"Stiffness"},
        {"id":9,"q":"Poisson's ratio is?","options":["Lateral/Axial strain","Stress/Strain","Force/Area","None"],"ans":"Lateral/Axial strain"},
        {"id":10,"q":"Deflection is?","options":["Displacement under load","Rotation","Stress","None"],"ans":"Displacement under load"},
        {"id":11,"q":"Column fails by?","options":["Buckling","Bending","Shear","None"],"ans":"Buckling"},
        {"id":12,"q":"Euler's formula is for?","options":["Long columns","Short columns","Beams","None"],"ans":"Long columns"},
        {"id":13,"q":"Reinforcement in RCC is?","options":["Steel bars","Wood","Plastic","None"],"ans":"Steel bars"},
        {"id":14,"q":"Pre-stressing means?","options":["Applying initial compression","Heating","Cooling","None"],"ans":"Applying initial compression"},
        {"id":15,"q":"Factor of safety = ?","options":["Ultimate/Working stress","Working/Ultimate","Both","None"],"ans":"Ultimate/Working stress"},
    ],
    "geotech": [
        {"id":1,"q":"Soil mechanics studies?","options":["Soil behavior","Rock only","Water only","None"],"ans":"Soil behavior"},
        {"id":2,"q":"Void ratio is?","options":["Volume of voids/solids","Solids/Voids","Water/Solids","None"],"ans":"Volume of voids/solids"},
        {"id":3,"q":"Liquid limit test uses?","options":["Casagrande apparatus","Sieve","Hydrometer","None"],"ans":"Casagrande apparatus"},
        {"id":4,"q":"SPT stands for?","options":["Standard Penetration Test","Soil Property Test","None","Simple"],"ans":"Standard Penetration Test"},
        {"id":5,"q":"Bearing capacity is?","options":["Load soil can support","Soil weight","Water level","None"],"ans":"Load soil can support"},
        {"id":6,"q":"Consolidation is?","options":["Settlement over time","Erosion","Weathering","None"],"ans":"Settlement over time"},
        {"id":7,"q":"Mohr's circle shows?","options":["Stress state","Strain only","Temperature","None"],"ans":"Stress state"},
        {"id":8,"q":"Pile foundation is for?","options":["Deep foundation","Shallow","Surface","None"],"ans":"Deep foundation"},
        {"id":9,"q":"Atterberg limits include?","options":["Liquid, Plastic, Shrinkage","Only Liquid","Only Plastic","None"],"ans":"Liquid, Plastic, Shrinkage"},
        {"id":10,"q":"Permeability measures?","options":["Water flow through soil","Strength","Density","None"],"ans":"Water flow through soil"},
        {"id":11,"q":"Clay has?","options":["Low permeability","High permeability","No permeability","None"],"ans":"Low permeability"},
        {"id":12,"q":"Compaction improves?","options":["Density","Moisture","Porosity","None"],"ans":"Density"},
        {"id":13,"q":"Retaining wall resists?","options":["Lateral earth pressure","Vertical load","Wind","None"],"ans":"Lateral earth pressure"},
        {"id":14,"q":"Water table is?","options":["Upper surface of groundwater","Bottom of well","Sea level","None"],"ans":"Upper surface of groundwater"},
        {"id":15,"q":"Sieve analysis finds?","options":["Particle size distribution","Moisture","Strength","None"],"ans":"Particle size distribution"},
    ],
    "surveying": [
        {"id":1,"q":"Surveying measures?","options":["Earth's surface features","Only height","Only area","None"],"ans":"Earth's surface features"},
        {"id":2,"q":"Leveling finds?","options":["Elevation differences","Angles only","Distance only","None"],"ans":"Elevation differences"},
        {"id":3,"q":"Theodolite measures?","options":["Angles","Only distance","Elevation","None"],"ans":"Angles"},
        {"id":4,"q":"Contour line connects?","options":["Equal elevation points","Different heights","Rivers","None"],"ans":"Equal elevation points"},
        {"id":5,"q":"Benchmark is?","options":["Reference point","Survey tool","Map type","None"],"ans":"Reference point"},
        {"id":6,"q":"GPS stands for?","options":["Global Positioning System","Ground Point Survey","None","General"],"ans":"Global Positioning System"},
        {"id":7,"q":"Chain surveying uses?","options":["Chain/Tape","Theodolite","GPS","None"],"ans":"Chain/Tape"},
        {"id":8,"q":"Prismatic compass measures?","options":["Bearing","Elevation","Distance","None"],"ans":"Bearing"},
        {"id":9,"q":"EDM stands for?","options":["Electronic Distance Measurement","Earth Data Map","None","Exact"],"ans":"Electronic Distance Measurement"},
        {"id":10,"q":"Scale of map is?","options":["Map distance/Ground distance","Ground/Map","Area ratio","None"],"ans":"Map distance/Ground distance"},
        {"id":11,"q":"Total station combines?","options":["Theodolite + EDM","Chain + Compass","GPS + Level","None"],"ans":"Theodolite + EDM"},
        {"id":12,"q":"Plane surveying assumes?","options":["Earth is flat","Earth is round","No assumption","None"],"ans":"Earth is flat"},
        {"id":13,"q":"Triangulation uses?","options":["Triangle network","Squares","Circles","None"],"ans":"Triangle network"},
        {"id":14,"q":"Remote sensing uses?","options":["Satellites/Aircraft","Ground survey","Chain","None"],"ans":"Satellites/Aircraft"},
        {"id":15,"q":"GIS stands for?","options":["Geographic Information System","Ground Info","None","General"],"ans":"Geographic Information System"},
    ],
}


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@quiz_engine_bp.route("/branches", methods=["GET"])
@token_required
def get_branches():
    """Return all available branches."""
    return jsonify({"branches": list(BRANCH_SUBJECTS.keys())}), 200


@quiz_engine_bp.route("/subjects/<branch>", methods=["GET"])
@token_required
def get_subjects(branch):
    """Return subjects for a given branch. Falls back to CS if unknown."""
    subjects = BRANCH_SUBJECTS.get(branch)
    if not subjects:
        subjects = BRANCH_SUBJECTS.get("Computer Science", [])
    return jsonify({"branch": branch, "subjects": subjects}), 200


@quiz_engine_bp.route("/quiz/<subject>", methods=["GET"])
@token_required
def get_quiz(subject):
    """Return quiz questions for a subject. Returns all available if < 15."""
    key = subject.strip().lower()
    questions = QUESTION_BANK.get(key)
    if not questions:
        return jsonify({"error": f"No questions found for subject: '{subject}'"}), 404

    # Deduplicate by id (safety)
    seen_ids = set()
    unique_qs = []
    for q in questions:
        if q["id"] not in seen_ids:
            seen_ids.add(q["id"])
            unique_qs.append(q)

    return jsonify({
        "subject": subject,
        "questions": unique_qs,
        "total": len(unique_qs),
    }), 200


@quiz_engine_bp.route("/submit", methods=["POST"])
@token_required
def submit_quiz():
    """Submit quiz score with feedback message."""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    score = data.get("score")
    total = data.get("total", 15)
    subject = data.get("subject")
    date = data.get("date")

    if score is None or not subject:
        return jsonify({"error": "Missing score or subject"}), 400

    # Feedback message
    percentage = (score / total * 100) if total > 0 else 0
    if percentage > 70:
        feedback = "Good job! You have a strong grasp of this subject."
    else:
        feedback = "Keep practicing! Review the topics and try again."

    # Save score
    user = find_user_by_email(g.current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    scores = user.get("scores", [])
    scores.append({
        "subject": subject,
        "score": score,
        "total": total,
        "date": date,
        "source": "quiz_engine",
    })
    update_user(g.current_user_email, {"scores": scores})

    return jsonify({
        "message": "Score saved successfully",
        "score": score,
        "total": total,
        "percentage": round(percentage),
        "feedback": feedback,
    }), 201
