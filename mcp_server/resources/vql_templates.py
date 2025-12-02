VQL_TEMPLATES = {
    "list_processes": "SELECT * FROM pslist()",
    "list_network": "SELECT * FROM netstat()",
    "list_clients": "SELECT * FROM clients()",
    "recent_alerts": "SELECT * FROM alerts() ORDER BY Timestamp DESC LIMIT 50",
    "filesystem_top": "SELECT * FROM vfs_listdir(client_id=$client_id, path=$path)",
}
