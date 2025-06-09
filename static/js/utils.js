const MEDIA_ALIAS = {
    "img": "Image",
    "sud": "Audio",
    "mov": "Video",
    "adv": "Story",
    "mdl": "Model",
    "mot": "Motion",
    "env": "Environment",
    "fbx": "FBX",
};

const SUBTYPE_ALIAS = {
    "cidol full": "Idol Card",
    "csprt full": "Support Card",
    "story-bg": "Background",
    "meishi_base full": "Namecard Bg",
    "pdrink": "P Drink",
    "pitem": "P Item",
    "skillcard": "Skillcard",
    "meishi_illust": "Namecard Elt",
};

const CHARACTER_ALIAS = {
    "hski": "Hanami Saki",
    "ttmr": "Tsukimura Temari",
    "fktn": "Fujita Kotone",
    "amao": "Arimura Mao",
    "kllj": "Katsuragi Lilja",
    "kcna": "Kuramoto China",
    "ssmk": "Shiun Sumika",
    "shro": "Shinosawa Hiro",
    "hrnm": "Himesaki Rinami",
    "hume": "Hanami Ume",
    "hmsz": "Hataya Misuzu",
    "jsna": "Juo Sena",
    "nasr": "Neo Asari",
};

const RARITY_ALIAS = {
    "-1-": "R",
    "-2-": "SR",
    "-3-": "SSR",
};

const SONG_ALIAS = {
    "all -001": "初",
    "all -002": "Campus mode!!",
    "all -003": "キミとセミブルー",
    "all -004": "冠菊",
    "all -005": "仮装狂騒曲",
    "all -006": "White Night! White Wish!",
    "all -007": "ハッピーミルフィーユ",
    "all -008": "古今東西ちょちょいのちょい",
    "all -009": "雪解けに",
    "char -001": "(1st Single)",
    "char -002": "(2nd Single)",
    "char -003": "(2024-25 Birthday Song)",
};

function dumpErrorToConsole(...args) {
    var name_of_parent_function = arguments.callee.caller.name;
    console.error("Error in " + name_of_parent_function);
    args.forEach((arg) => {
        console.error(arg);
    });
}

function subscribeToProgress(type, id, onUpdate) {
    const src = new EventSource(`/sse/${type.toLowerCase()}/${id}/progress`);

    src.onopen = function () {
        onUpdate("open", { type: type, id: id });
    };

    src.onerror = function (event) {
        onUpdate("error", {
            type: type,
            id: id,
            message: "Error while subscribing to progress stream",
            description: event.data || "Unknown error",
        });
        src.close();
    };

    src.onmessage = function (event) {
        const data = JSON.parse(event.data);
        onUpdate("update", data);
    };

    src.addEventListener("success", function (event) {
        const data = JSON.parse(event.data);
        onUpdate("success", data);
        src.close();
    });

    src.addEventListener("warning", function (event) {
        const data = JSON.parse(event.data);
        onUpdate("warning", data);
    });

    src.addEventListener("error", function (event) {
        const data = JSON.parse(event.data);
        onUpdate("error", data);
        src.close();
    });

    return src; // for external access
}

function getMediaBlobURL(type, id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "GET",
            url: `/api/${type.toLowerCase()}/${id}/bytestream`,
            xhrFields: { responseType: "arraybuffer" },

            success: function (data, status, request) {
                const mimetype = request.getResponseHeader("Content-Type");
                const mtime = request.getResponseHeader("Last-Modified");
                blob = new Blob([data], { type: mimetype });
                resolve({
                    url: URL.createObjectURL(blob),
                    mimetype: mimetype,
                    mtime: mtime.replace(/ GMT.*/, ""),
                });
            },

            error: function (...args) {
                dumpErrorToConsole(...args);
                blob = new Blob(["An error occurred while fetching media."], {
                    type: "text/plain",
                });
                reject({
                    url: URL.createObjectURL(blob),
                    mimetype: "text/plain",
                    mtime: "Unknown",
                });
            },
        });
    });
}
