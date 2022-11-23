import html

def escape(text):
    return html.escape(text)

class MessageCreator:
    def gitlab(self, webhook_request):
        kind = webhook_request.json["object_kind"]

        if kind == "push":
            project = escape(webhook_request.json["project"]["name"])
            ref = escape(webhook_request.json["ref"].split('/')[-1])
            user_name = escape(webhook_request.json["user_name"])
            message = "📢 New <b>{}</b> on <i>{} ({})</i> by {} 📢 \n".format(kind, project, ref, user_name)
            commits = webhook_request.json["commits"]
            for c in commits:
                message += "〰〰〰〰〰\n🔔 "+ escape(c["message"]) + " <i>({})</i>\n".format(escape(c["author"]["name"]))
        elif kind == "tag_push":
            project = escape(webhook_request.json["project"]["name"])
            ref = escape(webhook_request.json["ref"].split('/')[-1])
            user_name = escape(webhook_request.json["user_name"])
            message = "📢 New <b>{}</b> on <i>{}</i>({}) by {} 📢 \n".format(kind, project, ref, user_name)
        elif kind == "issue":
            project = escape(webhook_request.json["project"]["name"])
            user_name = escape(webhook_request.json["user"]["user_name"])
            message = "📢 New <b>{}</b> on <i>{}</i> by {} 📢 \n".format(kind, project, user_name)
            message += escape(webhook_request.json["object_attributes"]["title"])
        elif kind == "pipeline":
            project = escape(webhook_request.json["project"]["name"])
            user_name = escape(webhook_request.json["commit"]["author"]["name"])
            url = escape(webhook_request.json["commit"]["url"])
            ref = escape(webhook_request.json["object_attributes"]["ref"].split('/')[-1])
            message = '📢 New <b>pipeline</b> event for <a href="{}">push</a> on <i>{} ({})</i> by {} 📢 \n'.format(url, project, ref, user_name)
            builds = webhook_request.json["builds"]
            for b in builds:
                status = b['status']
                detailed_status = status
                if status == "success":
                    detailed_status = "success 🎉🥳"
                elif status == "created":
                    detailed_status = "created 🏗"
                elif status == "skipped":
                    detailed_status = "skipped 🖐"
                elif status == "failed":
                    detailed_status = "failed 🧟‍👊🏼"
                elif status == "pending":
                    detailed_status = "pending 🕓"
                    return False, "" # send no message that contains "pending" state
                elif status == "running":
                    detailed_status = "running 🛵"
                    return False, "" # send no message that contains "running" state
                elif status == "canceled":
                    detailed_status = "canceled 🚫"
                else:
                    detailed_status = escape(detailed_status)
                message += "➖ <b>{}</b> ({}): {}\n".format(b["name"], b["stage"], detailed_status)
        else:
            return False, ""

        return True, message

    def github(self, webhook_request):
        kind = webhook_request.headers['X-GitHub-Event']
        project = webhook_request.json["repository"]["name"]


        if kind == "push":
            ref = webhook_request.json["ref"].split('/')[-1]
            user_name = webhook_request.json["pusher"]['name']
            message = "📢 New <b>{}</b> on <i>{} ({})</i> by {} 📢 \n".format("Push", project, ref, user_name)
            commits = webhook_request.json["commits"]
            for c in commits:
                message += "〰〰〰〰〰\n🔔 "+ c["message"] + " <i>({})</i>\n".format(c["author"]["name"])
        elif kind == "create":
            ref = webhook_request.json["ref"]
            user_name = webhook_request.json["sender"]['login']
            message = "📢 New <b>{}</b> on <i>{}</i>({}) by {} 📢 \n".format(webhook_request.json['ref_type'], project, ref, user_name)
        else:
            return False, ""

        return True, message

    def new_gitlab(self, url, secret):
        return "Set this url in your gitlab webhook setting:\n" +\
                "URL: {}\nSecret Token: <code>{}</code>\n".format(url, secret) +\
                'Send /help_gitlab for more info.'
    
    def new_github(self, url, secret):
        return "Set this url in your github webhook setting:\n" +\
                "URL: {}\nSecret Token: <code>{}</code>\n".format(url, secret) +\
                'Send /help_github for more info.'
    
    def help_gitlab(self):
        return "1. Go to *your project* on the GitLab website\n" +\
                "2. Click on *setting*⚙ icon\n" +\
                "3. Click on *integrations*\n" +\
                "4. Enter *URL*, *Secret Token* and, check *Enable SSL verification*\n" +\
                "5. Modify *Trigger Check List* and click on *Add Webhook*"

    def help_github(self):
        return "1. Go to *your project* on the GitHub website\n" +\
                "2. Click on *⚙ Settings*\n" +\
                "3. Choose *Webhooks* from left menu\n" +\
                "4. Click on *Add Webhook* button\n" +\
                "5. Enter *URL*, *Secret Token* and, choose *application/json* for the Content type field\n" +\
                "6. Choose *Send me everything.*\n" +\
                "7. Check *Active* and click on *Add Webhook* button"
