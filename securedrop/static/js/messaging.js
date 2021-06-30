function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Temp: Investigate best way to sanitize plaintext messages prior to display
function sanitizeString(str) {
    str = str.replace(/[^a-z0-9áéíóúñü \.,_-]/gim,"");
    return str.trim();
}

function removeSendMsg() {
    if (document.getElementById("success-message")) {
        document.getElementById("success-message").value = "";
    }
}

function apiSend( method, url, token, req_body, fn_success_callback, get_response_body = false ) {
    var request = new XMLHttpRequest();
    request.open(method, url, true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
      if (request.readyState === 4 && request.status === 200) {
        if (get_response_body == true) {
            resp = JSON.parse(this.response)
        }
        fn_success_callback();
        console.log('ran success callback');
      } else if (request.status != 200) {
        // TODO: If error occurs, then we'd need to show some sort of error to the user.
        console.error("err occurred hitting securedrop API");
        console.error(request.status);
        console.error(request.readyState);
      }
    };

    if (req_body != null) {
        request.send(JSON.stringify(req_body));
    } else {
        request.send();
    }
}

async function onRegistrationSuccess(session) {
    console.log("registered successfully!");
    // We get a fresh sender cert at the beginning of every session
    getSenderCert(session);
    // We also get the server parameters
    getServerParams(session);
    await sleep(250);
    getAuthCredential(session);
}

function onPrekeySucccess(session, prekey_data) {
    console.log(`got some ${prekey_data}`)

    // TODO: show error to user if the below call to wasm fails
    session.process_prekey_bundle(
      prekey_data["registration_id"],
      prekey_data["identity_key"],
      prekey_data["journalist_uuid"],
      prekey_data["signed_prekey_id"],
      prekey_data["signed_prekey"],
      prekey_data["prekey_signature"]
      );
    console.log("processed prekey bundle successfully");

    document.getElementById("submit-doc-button").disabled = false;
}


function onReplySucccess(session, reply_data) {
    var token = session.token();
    if (reply_data["resp"] == 'NEW_MSG') {
        console.log("got new reply");
        var plaintext = session.sealed_sender_decrypt(
            reply_data["message"],
        );
        console.log(`decrypted new message!: ${plaintext}`);
        // At this point, we might want to store messages somewhere more persistent
        // (e.g. some local browser storage that works while in Private Browsing Mode).
        // Otherwise, when a user refreshes, their messages will be gone.
        // However, we do want this not to persist (should be the case in PBM) such
        // that on subsequent logins, the messages are also gone.

        // Security note: at this point we need to sanitize the plaintext prior to
        // displaying in the browser. For now we use sanitizeString, but we may
        // want to bring in another dependency for this.
        const reply_div = document.createElement("div");
        reply_div.className = "reply";
        const success_blquote = document.createElement("blockquote");
        success_blquote.textContent = sanitizeString(plaintext);
        reply_div.appendChild(success_blquote);
        document.getElementById("replies").appendChild(reply_div);

        // Now send confirmation.
        var message_uuid = reply_data["message_uuid"];
        apiSend( "POST", `http://127.0.0.1:8080/api/v2/messages/confirmation/${message_uuid}`, token, null, onConfirmationSuccess );
    }
}

function onMessageSendSuccess() {
    if (!document.getElementById("success-message")) {
        const success_div = document.createElement("div");
        success_div.id = "success-message"
        const success_emoji = document.createTextNode("sent! ✅");
        success_div.appendChild(success_emoji);
        document.getElementById("below-the-submit").prepend(success_div);
        setTimeout(removeSendMsg, 3000); // Remove this message in 3 seconds
        console.log("sent successfully!")
    }
}

function onGroupAddSuccess() {
    console.log("sent group deets to journalist");
}

function onConfirmationSuccess() {
    console.log(`sent confirmation of message on server`);
}

async function prepareSession( session, needs_registration, securedrop_group ) {
    console.log(`we need to register: ${needs_registration}`);

    if (needs_registration == true) {
        var keygen_data = session.generate();  // keygen_data just contains the public parts
        console.log(`signal key generation succeeded: ${keygen_data}`);
        var request = new XMLHttpRequest();
        var token = session.token();
        request.open("POST", "http://127.0.0.1:8080/api/v2/register", true);
        request.setRequestHeader("Content-Type", "application/json");
        request.setRequestHeader("Authorization", `Token ${token}`);

        request.onreadystatechange = async function () {
            if (request.readyState === 4 && request.status === 200) {
                await onRegistrationSuccess(session);
                console.log('finished registration callback');

            }
        };
        request.send(JSON.stringify(keygen_data));

        // In group world we need to:
        //   1. Form a group since - this is our first login!
        //   2. Fetch prekey bundles for each journalist in our group.
        //   3. Distribute the GroupMasterKey with our journalists.
        //   4. Now we can message!

        // Step 1. Form a group.
        var members = [
            { string: session.uuid()}
        ];
        var admins = []
        for (ind in securedrop_group) {
            admins.push({
                string: securedrop_group[ind]
            })
        };
        console.log(admins);

        // Note: we must have AuthCred to create the group.
        await sleep(2000);
        var public_group_data = session.create_group(members, admins);
        var group_request = new XMLHttpRequest();
        group_request.open("POST", "http://127.0.0.1:8080/api/v2/groups/new", true);
        group_request.setRequestHeader("Content-Type", "application/json");
        group_request.setRequestHeader("Authorization", `Token ${token}`);

        group_request.onreadystatechange = function () {
            if (group_request.readyState === 4 && group_request.status === 200) {
                console.log("created group successfully");
            }
        };
        group_request.send(JSON.stringify(public_group_data));

        await sleep(250);

        // Step 2. Fetch prekey bundles for each journalist in our group.
        var session2 = session;
        for (ind in securedrop_group) {
            var prekey_request = new XMLHttpRequest();
            var journalist_uuid = securedrop_group[ind];

            prekey_request.open("GET", `http://127.0.0.1:8080/api/v2/journalists/${journalist_uuid}/prekey_bundle`, true);
            prekey_request.setRequestHeader("Content-Type", "application/json");
            prekey_request.setRequestHeader("Authorization", `Token ${token}`);

            prekey_request.onreadystatechange = function () {
                if (prekey_request.readyState === 4 && prekey_request.status === 200) {
                    var prekey_data = JSON.parse(this.response)
                    onPrekeySucccess(session2, prekey_data);
                }
            };
            prekey_request.send();

            await sleep(1000);

            var ciphertext = session2.sealed_send_encrypted_group_key(journalist_uuid);
            console.log(`encrypted group key: ${ciphertext}`);
            var payload = {"message": ciphertext,};
            apiSend( "POST", `http://127.0.0.1:8080/api/v2/journalists/${journalist_uuid}/messages`, session2.token(), payload, onGroupAddSuccess );
        };

        // TODO: In the future, we may be registered, but not all these steps have necessarily succeeded.
        // When we log back in, we should pick up where we left off. For example, we don't attempt
        // to create the group again if we have it stored.
    } else {
        document.getElementById("submit-doc-button").disabled = false;
        // TODO: Get existing session from server
        // We get a fresh sender cert at the beginning of every session (even if not newly registered)
        getSenderCert(session);
        getServerParams(session);
        await sleep(250);
        getAuthCredential(session);
    }

    console.log(`user is registered, waiting for message send`);
}

function getSenderCert(session) {
    var request = new XMLHttpRequest();
    var token = session.token();
    request.open("GET", "http://127.0.0.1:8080/api/v2/sender_cert", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            var resp_data = JSON.parse(this.response);
            var result = session.get_cert_and_validate(resp_data["sender_cert"], resp_data["trust_root"]);
            console.log(`sender_cert result: ${result}`);
        }
    };
    request.send();
}

function getAuthCredential( session ) {
    var request = new XMLHttpRequest();
    var token = session.token();
    request.open("GET", "http://127.0.0.1:8080/api/v2/auth_credential", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            var resp_data = JSON.parse(this.response);
            var result = session.save_auth_credential(resp_data["auth_credential"]);
            console.log(`got auth_credential, result: ${result}`);
        }
    };
    request.send();
}

function getServerParams( session ) {
    var request = new XMLHttpRequest();
    var token = session.token();
    request.open("GET", "http://127.0.0.1:8080/api/v2/server_params", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            var resp_data = JSON.parse(this.response);
            var result = session.save_server_params(resp_data["server_public_params"]);
            console.log(`got server params, result: ${result}`);
        }
    };
    request.send();
}

function messageEncryptAndSend( session, securedrop_group ) {
    // Encrypt and send message for each group participant
    for (ind in securedrop_group) {
        var journalist_uuid = securedrop_group[ind];
        var message_text = document.getElementById("msg").value;
        // TODO: Don't do anything if message empty
        var ciphertext = session.group_sealed_sender_encrypt(journalist_uuid, message_text);
        console.log(`message text: ${message_text}`);
        console.log(`ciphertext: ${ciphertext}`);

        var payload = {"message": ciphertext,};
        console.log(`now sending to: ${journalist_uuid}`);
        apiSend( "POST", `http://127.0.0.1:8080/api/v2/journalists/${journalist_uuid}/messages`, session.token(), payload, onMessageSendSuccess );
    }

    // Now reset UI for next message
    document.getElementById("msg").value = "";
}

function messageDecryptAndSend( session ) {
    // Download
    var request = new XMLHttpRequest();
    var token = session.token();
    request.open("GET", "http://127.0.0.1:8080/api/v2/messages", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Authorization", `Token ${token}`);

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            var reply_data = JSON.parse(this.response);
            onReplySucccess(session, reply_data);
        }
    };
    request.send();
}
