### 23 Oct 2025

### _Progress_ 
Created chatbot using Langchain + Google-genai  
This have the access to database and can use SELECT queries only, bcuz it used "QuerySQLDatabaseTool" which only have permission of SELECT.  
This is for normal users.

### _Problem_
- Why i am trying to create CLI?  
I want to add an option for admins to update the schedule and inform students about class cancellation or rescheduling. 
    - Why i cant do this with llms?  
    Because we dont know what kind of query will LLM allow and that can alter the whole database, which is obviously risky

- Damn!! Why did i not think of this early!!!!  
I can create a separate chatbot for admins that will, show them the query its going to use. And only execute that if admin agrees,
    - If the query is wrong, then admin can write his own query. and that will be used. 

#### _By this i dont have to create a CLI.... DAMN!_