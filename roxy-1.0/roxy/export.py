from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import and_, or_, not_, select, delete

session_cache = {}

engine = create_engine("mysql://root:dr0w554p@localhost/roxyproxy")
metadata = MetaData(bind=engine, reflect=True)

requests = metadata.tables['requests']

where_parts = []
where_parts.append(requests.c.Id != None)
whereclause = and_(*where_parts)

stmt = select("*", whereclause=whereclause, order_by=[requests.c.Date])

result = stmt.execute()

print("RequestId\tSessionId\tDate\tUrl\tMimeType\tStatus\tArchive\tUserAgent\tSize\tIndexed\tReferrer\tUser\tSessionStart\tSessionEnd\tIpAddress")
	
for row in result:
	output = "req:" + str(row["Id"]) + "\tses:" + str(row["Session"]) + "\t" + str(row["Date"]) + "\t" 
	output = output + str(row["Url"]) + "\t" + str(row["MimeType"]) + "\t" + str(row["Status"]) + "\t" 
	output = output + str(row["Archive"]) + "\t" + str(row["UserAgent"]) + "\t" + str(row["Size"]) + "\t"
	output = output + str(row["Indexed"]) + "\t" + str(row["Referrer"]) + "\t"
	
	session = None
	
	try:
		session = session_cache[str(row["Session"])]
	except KeyError:
		sessions = metadata.tables['sessions']
		
		where_parts = []
		where_parts.append(sessions.c.Id == str(row["Session"]))
		whereclause = and_(*where_parts)
		
		ses_stmt = select("*", whereclause=whereclause)
		
		ses_result = ses_stmt.execute()
		
		for ses_row in ses_result:
			session = ses_row
			
		session_cache[str(row["Session"])] = session
		
	output += str(session["User"]) + "\t" + str(session["Start"]) + "\t" + str(session["End"]) + "\t"
	output += str(session["IpAddress"])

	print(output)