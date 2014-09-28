% rebase('base.tpl', title='Tournament Info')
<h1>Tournaments on {{date}}</h1>
<p>This template is working.</p>
% for row in cursor:
    <p><a href="../events/{{row['id']}}">MTGO {{row['metagame']}}</a></p>
