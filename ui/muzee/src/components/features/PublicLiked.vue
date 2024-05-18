<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'"
    color="purple-lighten-4">
    <span v-if="state === 'idle'">

      <!-- form -->
      <!-- no form -->

      <!-- feature playlist -->
      <div v-if="featureEnabled" class="mx-auto pb-3">
        <v-card class="d-flex justify-space-between flex-wrap" style="justify-content: center !important;">
          <div>

            <v-card-title class="text-h5">
              Public Liked
            </v-card-title>

            <v-card-subtitle>🎸 Here is what I listen to...</v-card-subtitle>

            <v-card-actions>
              <v-btn prepend-icon="mdi-spotify" class="mx-2" color="green" @click="openPlaylist">Open</v-btn>
            </v-card-actions>
          </div>

          <v-avatar class="ma-3" rounded="0" size="125">
            <v-img :src="playlistImage" lazy-src="https://i.imgur.com/N1svi4r.png">
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
                </div>
              </template>
            </v-img>
          </v-avatar>
        </v-card>
      </div>

      <!-- actions -->
      <v-card-actions class="justify-center py-2">
        <v-btn variant="text" @click="toggleFeature" :color="(featureEnabled ? 'red' : 'purple-lighten-2')" class="ma-2"
          size="large" :prepend-icon="featureEnabled ? 'mdi-sleep' : 'mdi-lightbulb-on'">
          <span>{{ featureEnabled ? 'Disable' : 'Enable' }} Public Liked</span>
        </v-btn>
      </v-card-actions>

    </span>
  </v-card>
</template>

<script>

export default {
  async mounted() {
    this.featureEnabled = this.enabledFeatures.includes(this.featureKey);

    if (this.featureEnabled) {
      const js = await this.api.featureDetails({ key: this.featureKey });

      this.playlistId = js.playlist;
      this.playlistImage = js.image || 'https://i.imgur.com/N1svi4r.png';
    }
  },

  props: ['feature', 'enabledFeatures'],

  data() {
    return {
      // config
      featureKey: 'public-liked',

      // activation status
      featureEnabled: false,


      // --------------------------------------
      state: 'idle',  // idle, done, error
      playlistName: '',
      playlistId: '',
      playlistImage: ''
    };
  },

  methods: {
    async toggleFeature() {
      this.$emit("start-loading");

      const js = await this.api.togglePublicLiked({
        enabled: !this.featureEnabled,
        timezone_offset: new Date().getTimezoneOffset()
      });

      this.$emit("feature-toggle", 'public-liked', !this.featureEnabled)
      this.$emit("stop-loading");

      if (js.error) {
        this.$emit("display-error", js.error);
        return
      }

      this.featureEnabled = !this.featureEnabled;
      this.playlistId = js.playlist;
      this.playlistImage = js.image || "https://i.imgur.com/N1svi4r.png";
    },

    openPlaylist() {
      window.open(`spotify:user:spotify:playlist:${this.playlistId}`, '_blank')
    },
  },

}

</script>

<style>
.bold-picked {
  font-weight: bold;
  color: #d27ddf;
}
</style>
