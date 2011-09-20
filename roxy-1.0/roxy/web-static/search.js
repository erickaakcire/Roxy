$.ajaxSetup ({
    cache: false
});

function flagNormal(doc_id)
{
	$.get("/set_interesting.xml?id=" + doc_id + "&interesting=false");
}

function flagInteresting(doc_id)
{
	$.get("/set_interesting.xml?id=" + doc_id + "&interesting=true");
}

function searchHistory()
{
	var find_text = $("input#find").val();
	var row_count = $("input#count").val();

	var user = $("input#user_constraint").val();
	var start = $("input#start_constraint").val();
	
	if (start !== "")
	{
		start = start + "T00:00:00.000Z";
	}	
	var end = $("input#end_constraint").val();

	if (end !== "")
	{
		end = end + "T23:59:59.999Z";
	}

	var url = $("input#url_constraint").val();
	
	var referrer = $("input#referrer_constraint").val();

	var search_terms = $("input#search_constraint").val();

	var sort = $("select#sort_by").val();

	var query = "";
	
	if ($('#body_check').attr('checked'))
	{
		query = query + "text_content:\"" + find_text + "\"";
	}

	if ($('#title_check').attr('checked'))
	{
		if (query !== "")
		{
			query = query + " AND ";
		}
			
		query = query + "title:\"" + find_text + "\"";
	}

	if ($('#search_check').attr('checked'))
	{
		if (query !== "")
		{
			query = query + " AND ";
		}
			
		query = query + "search_terms:\"" + find_text + "\"";
	}

	if (user !== "")
	{
		if (query !== "")
		{
			query = query + " AND ";
		}

		query = query + "user_id:\"" + user + "\"";
	}
	
	if (url !== "")
	{
		if (query !== "")
		{
			query = query + " AND ";
		}

		query = query + " url:" + url;
	}
	
	if (referrer !== "")
	{
		if (query !== "")
		{
			query = query + " AND ";
		}
		
		query = query + " referrer:" + referrer;
	}

	if (search_terms !== "")
	{
		if (query !== "")
		{
			query = query + " AND ";
		}
		
		query = query + " search_terms:" + search_terms;
	}
	
	if (start !== "")
	{
		if (query !== "")
		{
			query = query + " AND ";
		}	

		query = query + "fetch_date:[" + start + " TO ";
		
		if (end !== "")
		{
			query = query + end;
		}
		else
		{
			query = query + "NOW";
		}
			
		query = query + "]";
	}
	
	if ($('#flag_check').attr('checked'))
	{
		if (query !== "")
		{
			query = query + " AND ";
		}
			
		query = query + "is_interesting:true";
	}

	
	query = "(" + query + ")";
	
	if (query !== "()")
	{
		$("div#search-results").load("/search.xml?query=" + escape(query) + "&rows=" + escape(row_count) + "&sort=" + escape(sort), function(response, status, xhr) 
		{
			if (status === "error") 
			{
				var msg = "Sorry but there was an error: ";
				$('div#search-results').html(msg + xhr.status + " " + xhr.statusText);
			}
		});
	}
}

$(function() 
{
	$("a.search_button").corner("5px");
	$("#start_constraint").datepicker({dateFormat: 'yy-mm-dd'});
	$("#end_constraint").datepicker({dateFormat: 'yy-mm-dd'});
});
