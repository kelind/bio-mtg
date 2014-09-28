<h1>Data for Tournament {{eventid}} (MTGO {{info['format']}} {{info['metagame']}})</h1>
<p>Event date: {{date}}</p>
<!-- bracket -->
<h2>Top Participants</h2>
<ol>
%for row in cursor:
    <li><a href="../players/{{row['userid']}}">{{row['name']}}</a> ({{row['wins']}} - {{row['losses']}})</li>
%end
</ol>
