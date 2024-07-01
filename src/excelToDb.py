import pandas as pd 
import sqlite3

xcelPath = "/Users/karolinaryzka/Documents/tool_course-scheduling/testExcelFile.xlsx"
df = pd.read_excel(xcelPath)

dbPath = "/Users/karolinaryzka/Documents/tool_course-scheduling/test.db"
conn = sqlite3.connect(dbPath)

table = "names"
df.to_sql(table, conn, if_exists='replace', index=False)

conn.close()

