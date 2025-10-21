## About Campus Chatbot

**Campus Chatbot** is an intelligent assistant designed to answer schedule-related queries for your college in natural language.  
It helps users get instant answers to questions like:

- Which classes are free right now?  
- Which classrooms with smart boards are available?  
- Where is the class of IIoT-B1 right now?  
- What is the schedule for IIoT-B1 today, tomorrow, or any specific day?  
- Are there any classes cancelled or rescheduled today?  

For this, the chatbot supports **real-time updates** via a **Command-Line Interface (CLI)**, allowing admins to update, reschedule, or cancel classes for any given day.

Currently, major timetable changes must be manually updated in the database by the developer.  
Future updates will include an option to **upload data directly** following a predefined database schema.

___Campus Chatbot is being developed to reduce the confusion around class schedules and help students get information instantly, without checking whatsapp groups or asking CRs and teachers.___


### How should my database look like?
Name: _campus_schedule_   
Tables:   
- Rooms- `room_id`, `room_name`, `has_smartboard`
- Schedule- `day`, `room_id`, `batch`, `semster`, `group`, `subject_code`, `subject_name`, `teacher_name`, `start_time`, `end_time`



### LangChain workflow
- A model will recieve user input query and output a SQL query
- Then that SQL query will get executed and
- The output from 2nd step will be given as input along with users original query to another model that will respond to user in natural language