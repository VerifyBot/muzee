// are we on https?
const isHttps = window.location.protocol === "https:";

function keepOnly(obj, keys) {
  let newObj = {};

  for (let key of keys) {
    newObj[key] = obj[key];
  }

  return newObj;
}

class ApiClient {
  async beforeSendResponse(resp) {
    return resp;
  }

  async request(method, endpoint, options = {}) {
    options.method = method;

    endpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

    const token = localStorage.getItem(this.tokenName);

    let add_header = token ? { Authorization: token } : {};

    options.headers = options.headers
      ? { ...options.headers, ...add_header }
      : add_header;

    options.headers["accept"] = "application/json";

    let resp;
    try {
      resp = await fetch(`${this.baseUrl}${endpoint}`, options);
    } catch {
      resp = { error: "network" };
    }

    //  is it 401 unauthorized? if yes redirect to /connect
    // and add the path to the localstorage
    if (resp?.status === 401) {
      console.log("401 unauthorized");
      localStorage.setItem("after_path", window.location.pathname);

      const url = this.baseUrl + "/oauth2/connect";
      this.disableAll = true;
      let r = await fetch(url);
      const js = await r.json();
      location.href = js.redirect_url;
      console.log("REDIRECTED TO " + js.redirect_url);
      return;
    }

    return await this.beforeSendResponse(resp);
  }

  // override this method to add some logic before the request
  async beforeRequest(method, endpoint, options) {
    return this.request(method, endpoint, options);
  }

  async get(endpoint, options = {}) {
    return this.beforeRequest("GET", endpoint, options);
  }

  async post(endpoint, body = {}, options = {}) {
    options.body = body ? JSON.stringify(body) : options.body;

    return this.beforeRequest("POST", endpoint, options);
  }
}

class MuzeeAPI extends ApiClient {
  baseUrl = isHttps ? "https://muzee.nirush.me" : "http://192.168.50.73:6969";
  tokenName = "muzeeToken";

  async redirectToLogin() {
    // make sure the server is alive first
    const url = `${this.baseUrl}/health`;

    try {
      await fetch(url);
    } catch (e) {
      return "down";
    }

    // server is up
    window.location.href = `${this.baseUrl}/oauth2/connect`;
  }

  async beforeSendResponse(resp) {
    if (resp?.error === "network") return resp;

    let js = await resp.json();
    console.log(js);

    if (js.error === "unauthorized") {
      localStorage.removeItem("token");
      this.redirectToLogin();
      return;
    }

    return js;
  }

  async beforeRequest(method, endpoint, options) {
    console.log("running before request")
    options.headers = options.headers || {};
    options.headers.Timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return super.beforeRequest(method, endpoint, options);
  }

  async status() {
    return await this.get("/status");
  }

  async generatePlaylist(data) {
    return await this.post("/generate_playlist", data);
  }

  async toggleDailySmash(data) {
    return await this.post("/toggle_daily_smash", data);
  }

  async featureDetails(data) {
    return await this.post("/feature_details", data);
  }

  async languageFilter(data) {
    return await this.post("/language_filter", data);
  }

  async togglePublicLiked(data) {
    return await this.post("/toggle_public_liked", data);
  }

  async toggleLiveWeather(data) {
    return await this.post("/toggle_live_weather", data);
  }
}

// some other file does "import { ApiClient } from './api.js'", so:
export { MuzeeAPI };
