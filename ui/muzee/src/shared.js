//
export const API_URL =
  // is https
  window.location.protocol === "https:"
    ? "https://muzee.nirush.me"
    : "http://192.168.50.73:6969";

    
const shared = {
  API_URL,
  async request(endpoint, jsonCallback, errorCallback, options) {
    const url = API_URL + endpoint;

    let auth = this.auth || localStorage.getItem("auth") || null;

    try {
      let resp = await fetch(url, {
        headers: auth
          ? {
              auth: auth,
              "content-type": "application/json",
            }
          : { "content-type": "application/json" },
        ...options,
      });

      //  is it 401 unauthorized? if yes redirect to /connect
      // and add the path to the localstorage
      if (resp.status === 401) {
        console.log("401 unauthorized");
        localStorage.setItem("after_path", window.location.pathname);

        const url = API_URL + "/oauth2/connect";
        this.disableAll = true;
        let resp = await fetch(url);
        const js = await resp.json();
        location.href = js.redirect_url;
      }

      if (jsonCallback) return await jsonCallback(await resp.json());
    } catch (err) {
      if (errorCallback) errorCallback(err);
    }
  },
};

export default shared;
