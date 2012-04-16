function(doc) {
    function clone(obj){
        if(obj == null || typeof(obj) != 'object')
            return obj;
        var temp = obj.constructor(); // changed
        for(var key in obj)
            temp[key] = clone(obj[key]);
        return temp;
    }
    if (doc.xmlns == 'http://code.javarosa.org/devicereport') {
        var logged_in_user = "unknown";
        for (var i in doc.form.log_subreport.log) {
            // need to clone because you can't set the property on the actual doc
            var entry = clone(doc.form.log_subreport.log[i]);
            entry.version = doc.form.app_version;
            entry.device_id = doc.form.device_id;

            if(entry.type == 'login')
                logged_in_user = entry.msg.substring(entry.msg.indexOf('-') + 1);
            entry.user = logged_in_user;

            if (entry.type && entry['@date']) {
                // Basic
                emit([doc.domain, "basic", entry['@date']], entry);

                // Single Parameters
                emit([doc.domain, "username", logged_in_user, entry['@date']], entry);
                emit([doc.domain, "tag", entry.type, entry['@date']], entry);
                emit([doc.domain, "device", doc.form.device_id, entry['@date']], entry);

                // Coupled Parameters
                emit([doc.domain, "tag_username", entry.type, logged_in_user, entry['@date']], entry);
                emit([doc.domain, "tag_device", entry.type, doc.form.device_id, entry['@date']], entry);
                emit([doc.domain, "username_device", logged_in_user, doc.form.device_id, entry['@date']], entry);

                // Tripled Parameters
                emit([doc.domain, "tag_username_device", entry.type, logged_in_user, doc.form.device_id, entry['@date']], entry);
            }

        }
    }
}