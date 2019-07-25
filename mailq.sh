hostname="$(/bin/hostname)";
qSize="$(mailq | grep -c "^[A-F0-9]")";
qLimit="50000";  #if the queue is larger then this number, an email will be sent to the $sendTo email address
from="sendr@example.com"
to="progressiveht@hindustantimes.com"
also_to="receiver@example.com"
############## There should be no need to edit bellow this line ##############

if [ $qSize -gt $qLimit ]; then
echo  "There are "$qSize" emails in the mail queue" | mailx  -s "*ALERT* - Mail queue on '"$hostname"' exceeds limit"  -r "$from" -t "$to" "$also_to"
fi
