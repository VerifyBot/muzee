<template>
  <iframe v-if="_playlistId" style="border-radius:12px" :src="'https://open.spotify.com/embed/playlist/' + _playlistId"
    width="100%" height="152" frameBorder="0" allowfullscreen=""
    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
  <v-skeleton-loader v-else type="card"></v-skeleton-loader>

  <!-- <v-card class="d-flex justify-center align-center pr-2" style="justify-content: center !important;">
          <div>
            <v-card-title class="py-0">
              {{ playlistTitle }}
            </v-card-title>

            <v-card-subtitle>{{ playlistDescription }}</v-card-subtitle>

            <v-card-actions class="mt-5">
              <v-btn prepend-icon="mdi-spotify" class="mx-2" color="green" @click="openPlaylist">Open</v-btn>
            </v-card-actions>
          </div>
          <v-img :src="playlistImage" lazy-src="https://i.imgur.com/N1svi4r.png" max-height="150">
            <template v-slot:placeholder>
              <div class="d-flex align-center justify-center fill-height">
                <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
              </div>
            </template>
</v-img>
</v-card> -->
</template>

<script>

export default {
  props: ['title', 'description', 'playlistId', 'playlistImage', 'newDelay'],

  data() {
    return {
      playlistTitle: this.title,
      playlistDescription: this.description,
      _playlistId: this.playlistId,
    };
  },

  async mounted() {

    // this is a hack to force the iframe to reload
    // because spotify doesn't render the new playlist
    // fast enough, it needs ~2s to display an embed.
    console.log(Boolean(this.newDelay), this.newDelay)
    if (this.newDelay) {
      this._playlistId = '';
      console.log("starting")
      await new Promise((resolve) => setTimeout(resolve, 2000));
      console.log("after 2")
      let tid = this.playlistId;
      this._playlistId = '';
      await this.$nextTick();
      console.log("after tick")
      this._playlistId = tid;
    } else {
      console.log(`Setting to ${this.playlistId}`)
      this._playlistId = this.playlistId;
    }
  },

  methods: {
    openPlaylist() {
      window.open(`spotify:user:spotify:playlist:${this.playlistId}`, '_blank')
    },
  },
};

</script>