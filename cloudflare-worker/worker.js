export default {
    async fetch(request, env, ctx) {
        const config = {
            BOT_TOKEN: env.BOT_TOKEN,
            BOT_SECRET: env.BOT_SECRET,
            BOT_ADMIN_ID: env.BOT_ADMIN_ID,
            GIT_WEBHOOK_KEY: env.GIT_WEBHOOK_KEY,
            GIT_WEBHOOK_BASE_URL: env.GIT_WEBHOOK_BASE_URL,
            WEBHOOK_PATH: "/bot",
        };

        const messageCreator = new MessageCreator();
        const handlers = createHandlers(config, messageCreator);
        const url = new URL(request.url);

        if (url.pathname === config.WEBHOOK_PATH) {
            return handlers.webhook(request, ctx);
        } else if (url.pathname === "/ping") {
            return new Response("pong");
        // } else if (url.pathname === "/registerWebhook") {
        //     return handlers.registerWebhook(url);
        // } else if (url.pathname === "/unregisterWebhook") {
        //     return handlers.unregisterWebhook();
        } else if (url.pathname.match(/^\/gitlab\/.+$/)) {
            const id = url.pathname.split("/gitlab/")[1];
            return handlers.gitlab(request, id, ctx);
        } else if (url.pathname.match(/^\/github\/.+$/)) {
            const id = url.pathname.split("/github/")[1];
            return handlers.github(request, id, ctx);
        } else {
            return new Response("No handler for this request");
        }
    },
};

function createHandlers(config, messageCreator) {
    return {
        async webhook(request, ctx) {
            if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== config.BOT_SECRET) {
                return new Response("Unauthorized", { status: 403 });
            }

            const update = await request.json();
            ctx.waitUntil(handleUpdate(update, config, messageCreator));
            return new Response("Ok");
        },

        async registerWebhook(requestUrl) {
            const webhookUrl = `${requestUrl.protocol}//${requestUrl.hostname}${config.WEBHOOK_PATH}`;
            const r = await fetch(apiUrl("setWebhook", {
                url: webhookUrl,
                secret_token: config.BOT_SECRET,
            })).then(res => res.json());

            return new Response("ok" in r && r.ok ? "Ok" : JSON.stringify(r, null, 2));
        },

        async unregisterWebhook() {
            const r = await fetch(apiUrl("setWebhook", { url: "" })).then(res => res.json());
            return new Response("ok" in r && r.ok ? "Ok" : JSON.stringify(r, null, 2));
        },

        async gitlab(request, id, ctx) {
            if (!request.headers.get("X-Gitlab-Token")) {
                return new Response("The 'Secret Token' is not in the request", { status: 400 });
            }

            const bodyText = await request.text();
            const token = await getToken(id, config.GIT_WEBHOOK_KEY);

            if (request.headers.get("X-Gitlab-Token") !== token) {
                return new Response("Unauthorized", { status: 403 });
            }

            const gitlabRequest = JSON.parse(bodyText);
            const [canSend, message] = messageCreator.gitlab(gitlabRequest);

            if (canSend) {
                const chatId = parseChatId(id);
                ctx.waitUntil(
                    logText(`gitlab ${chatId}`, config)
                        .then(() => sendHtml(chatId, message))
                );
            }

            return new Response("Ok", { status: 200 });
        },

        async github(request, id, ctx) {
            if (!request.headers.get("X-Hub-Signature")) {
                return new Response("The 'Secret Token' is not in the request", { status: 400 });
            }

            const bodyBuffer = await request.arrayBuffer();
            const token = await getToken(id, config.GIT_WEBHOOK_KEY);
            const signature = request.headers.get("X-Hub-Signature");

            const isValid = await validateGithubSignature(token, bodyBuffer, signature);
            if (!isValid) {
                return new Response("Unauthorized", { status: 403 });
            }

            const bodyText = new TextDecoder().decode(bodyBuffer);
            const githubRequest = JSON.parse(bodyText);
            const [canSend, message] = messageCreator.github(githubRequest);

            if (canSend) {
                const chatId = parseChatId(id);
                ctx.waitUntil(
                    logText(`github ${chatId}`, config)
                        .then(() => sendHtml(chatId, message))
                );
            }

            return new Response("Ok", { status: 200 });
        },
    };

    async function handleUpdate(update, config, messageCreator) {
        if ("message" in update) {
            const message = update.message;
            const text = message.text || "";
            const chatId = message.chat.id;
            const username = message.from?.username || "unknown";
            const chatTitle = message.chat?.title || "private";

            // Parse command
            const commandMatch = text.match(/^\/(\w+)/);
            if (commandMatch) {
                const command = commandMatch[1];

                switch (command) {
                    case "start":
                        await logText(`start ${chatId} ${username} ${chatTitle}`, config);
                        await handleNewGitlab(chatId, config, messageCreator, false);
                        await handleNewGithub(chatId, config, messageCreator, false);
                        break;

                    case "new_gitlab":
                        await logText(`new_gitlab ${chatId} ${username} ${chatTitle}`, config);
                        await handleNewGitlab(chatId, config, messageCreator, true);
                        break;

                    case "new_github":
                        await logText(`new_github ${chatId} ${username} ${chatTitle}`, config);
                        await handleNewGithub(chatId, config, messageCreator, true);
                        break;

                    case "help_gitlab":
                        await logText(`help_gitlab ${chatId} ${username} ${chatTitle}`, config);
                        await sendMarkdownV2(chatId, messageCreator.helpGitlab());
                        break;

                    case "help_github":
                        await logText(`help_github ${chatId} ${username} ${chatTitle}`, config);
                        await sendMarkdownV2(chatId, messageCreator.helpGithub());
                        break;

                    default:
                        // Echo for unknown commands
                        const echoText = `Echo:\n${text}`;
                        await sendPlainText(chatId, echoText);
                }
            } else if (text) {
                // Echo if not a command
                const echoText = `Echo:\n${text}`;
                await sendPlainText(chatId, echoText);
            }
        }
    }

    async function handleNewGitlab(chatId, config, messageCreator, logEvent) {
        if (logEvent) {
            await logText(`new_gitlab triggered for ${chatId}`, config);
        }
        const id = formatId(chatId);
        const token = await getToken(id, config.GIT_WEBHOOK_KEY);
        const url = `${config.GIT_WEBHOOK_BASE_URL}/gitlab/${id}`;
        const message = messageCreator.newGitlab(url, token);
        await sendHtml(chatId, message);
    }

    async function handleNewGithub(chatId, config, messageCreator, logEvent) {
        if (logEvent) {
            await logText(`new_github triggered for ${chatId}`, config);
        }
        const id = formatId(chatId);
        const token = await getToken(id, config.GIT_WEBHOOK_KEY);
        const url = `${config.GIT_WEBHOOK_BASE_URL}/github/${id}`;
        const message = messageCreator.newGithub(url, token);
        await sendHtml(chatId, message);
    }

    async function sendPlainText(chatId, text) {
        return fetch(apiUrl("sendMessage", { chat_id: chatId, text })).then(res => res.json());
    }

    async function sendMarkdownV2(chatId, text) {
        return fetch(apiUrl("sendMessage", {
            chat_id: chatId,
            text,
            parse_mode: "MarkdownV2",
        })).then(res => res.json());
    }

    async function sendHtml(chatId, text) {
        return fetch(apiUrl("sendMessage", {
            chat_id: chatId,
            text,
            parse_mode: "HTML",
        })).then(res => res.json());
    }

    async function logText(line, config) {
        const timestamp = new Date().toISOString();
        const logMessage = `${timestamp} ${line}`;
        try {
            await sendPlainText(config.BOT_ADMIN_ID, logMessage);
        } catch (e) {
            console.error("Failed to send log to admin:", e);
        }
    }

    function apiUrl(methodName, params = null) {
        const query = params ? "?" + new URLSearchParams(params) : "";
        return `https://api.telegram.org/bot${config.BOT_TOKEN}/${methodName}${query}`;
    }

    function formatId(chatId) {
        if (chatId < 0) {
            return "n" + String(-chatId);
        } else {
            return "p" + String(chatId);
        }
    }

    function parseChatId(id) {
        const chatId = id.substring(1);
        if (id[0] === 'n') {
            return -1 * parseInt(chatId);
        } else {
            return parseInt(chatId);
        }
    }

    async function getToken(id, key) {
        const hashInput = String(id) + key;
        return await md5(hashInput);
    }

    async function validateGithubSignature(token, bodyBuffer, signature) {
        const secretBytes = new TextEncoder().encode(token);
        const key = await crypto.subtle.importKey(
            "raw",
            secretBytes,
            { name: "HMAC", hash: "SHA-1" },
            false,
            ["sign"]
        );
        const signatureBuffer = await crypto.subtle.sign(
            "HMAC",
            key,
            bodyBuffer
        );
        const hexSignature = "sha1=" + Array.from(new Uint8Array(signatureBuffer))
            .map(b => b.toString(16).padStart(2, "0"))
            .join("");

        return hexSignature === signature;
    }
}

async function md5(message) {
    const msgUint8 = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8);
    
    return Array.from(new Uint8Array(hashBuffer))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

function escapeMarkdown(str, except = "") {
    const all = "_*[]()~`>#+-=|{}.!\\".split("").filter(c => !except.includes(c));
    const regExSpecial = "^$*+?.()|{}[]\\";
    const regEx = new RegExp(
        "[" + all.map(c => (regExSpecial.includes(c) ? "\\" + c : c)).join("") + "]",
        "gim"
    );
    return str.replace(regEx, "\\$&");
}

function escape(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
}

class MessageCreator {
    gitlab(webhookRequest) {
        const kind = webhookRequest.json["object_kind"];

        let message;

        if (kind === "push") {
            const project = escape(webhookRequest.json["project"]["name"]);
            const ref = escape(webhookRequest.json["ref"].split('/').pop());
            const userName = escape(webhookRequest.json["user_name"]);
            message = `📢 New <b>${kind}</b> on <i>${project} (${ref})</i> by ${userName} 📢 \n`;
            const commits = webhookRequest.json["commits"];
            for (const c of commits) {
                message += `〰〰〰〰〰\n🔔 ${escape(c["message"])} <i>(${escape(c["author"]["name"])})</i>\n`;
            }
        } else if (kind === "tag_push") {
            const project = escape(webhookRequest.json["project"]["name"]);
            const ref = escape(webhookRequest.json["ref"].split('/').pop());
            const userName = escape(webhookRequest.json["user_name"]);
            message = `📢 New <b>${kind}</b> on <i>${project}</i>(${ref}) by ${userName} 📢 \n`;
        } else if (kind === "issue") {
            const project = escape(webhookRequest.json["project"]["name"]);
            const userName = escape(webhookRequest.json["user"]["user_name"]);
            message = `📢 New <b>${kind}</b> on <i>${project}</i> by ${userName} 📢 \n`;
            message += escape(webhookRequest.json["object_attributes"]["title"]);
        } else if (kind === "pipeline") {
            const project = escape(webhookRequest.json["project"]["name"]);
            const userName = escape(webhookRequest.json["commit"]["author"]["name"]);
            const url = escape(webhookRequest.json["commit"]["url"]);
            const ref = escape(webhookRequest.json["object_attributes"]["ref"].split('/').pop());
            message = `📢 New <b>pipeline</b> event for <a href="${url}">push</a> on <i>${project} (${ref})</i> by ${userName} 📢 \n`;
            const builds = webhookRequest.json["builds"];
            for (const b of builds) {
                let status = b['status'];
                let detailedStatus = status;
                if (status === "success") {
                    detailedStatus = "success 🎉🥳";
                } else if (status === "created") {
                    detailedStatus = "created 🏗";
                } else if (status === "skipped") {
                    detailedStatus = "skipped 🖐";
                } else if (status === "failed") {
                    detailedStatus = "failed 🧟‍👊🏼";
                } else if (status === "pending") {
                    detailedStatus = "pending 🕓";
                    return [false, ""]; // send no message that contains "pending" state
                } else if (status === "running") {
                    detailedStatus = "running 🛵";
                    return [false, ""]; // send no message that contains "running" state
                } else if (status === "canceled") {
                    detailedStatus = "canceled 🚫";
                } else {
                    detailedStatus = escape(detailedStatus);
                }
                message += `➖ <b>${b["name"]}</b> (${b["stage"]}): ${detailedStatus}\n`;
            }
        } else {
            return [false, ""];
        }

        return [true, message];
    }

    github(webhookRequest) {
        const kind = webhookRequest.headers['X-GitHub-Event'];
        const project = webhookRequest.json["repository"]["name"];

        let message;

        if (kind === "push") {
            const ref = webhookRequest.json["ref"].split('/').pop();
            const userName = webhookRequest.json["pusher"]['name'];
            message = `📢 New <b>Push</b> on <i>${project} (${ref})</i> by ${userName} 📢 \n`;
            const commits = webhookRequest.json["commits"];
            for (const c of commits) {
                message += `〰〰〰〰〰\n🔔 ${c["message"]} <i>(${c["author"]["name"]})</i>\n`;
            }
        } else if (kind === "create") {
            const ref = webhookRequest.json["ref"];
            const userName = webhookRequest.json["sender"]['login'];
            message = `📢 New <b>${webhookRequest.json['ref_type']}</b> on <i>${project}</i>(${ref}) by ${userName} 📢 \n`;
        } else {
            return [false, ""];
        }

        return [true, message];
    }

    newGitlab(url, secret) {
        return `Set this url in your gitlab webhook setting:\nURL: <code>${url}</code>\nSecret Token: <code>${secret}</code>\nSend /help_gitlab for more info.`;
    }

    newGithub(url, secret) {
        return `Set this url in your github webhook setting:\nURL: <code>${url}</code>\nSecret Token: <code>${secret}</code>\nSend /help_github for more info.`;
    }

    helpGitlab() {
        return "1. Go to *your project* on the GitLab website\n" +
            "2. Click on *setting*⚙ icon\n" +
            "3. Click on *integrations*\n" +
            "4. Enter *URL*, *Secret Token* and, check *Enable SSL verification*\n" +
            "5. Modify *Trigger Check List* and click on *Add Webhook*";
    }

    helpGithub() {
        return "1. Go to *your project* on the GitHub website\n" +
            "2. Click on *⚙ Settings*\n" +
            "3. Choose *Webhooks* from left menu\n" +
            "4. Click on *Add Webhook* button\n" +
            "5. Enter *URL*, *Secret Token* and, choose *application/json* for the Content type field\n" +
            "6. Choose *Send me everything.*\n" +
            "7. Check *Active* and click on *Add Webhook* button";
    }
}
