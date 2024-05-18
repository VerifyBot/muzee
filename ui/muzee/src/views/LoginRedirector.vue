<template>
  <div>
    📲 Redirecting you to Spotify...
  </div>
</template>

<script>
import { API_URL } from '../shared.js';

export default {
  async beforeCreate() {
    // if already has auth
    localStorage.removeItem("auth");

    console.log("401 unauthorized");
    const url = API_URL + "/oauth2/connect";
    this.disableAll = true;
    let resp = await fetch(url);
    const js = await resp.json();
    location.href = js.redirect_url;
  }
}

</script>