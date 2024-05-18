<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'"
    color="purple-lighten-4">
    <span v-if="state === 'idle'">

      <!-- form -->
      <v-card-text class="pb-0">
        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-hours-24</v-icon>
          Run Daily At
          <span class="bold-picked ml-2" style="font-size: 1.7rem"
            v-text="String(Math.floor(updateAt / 60)).padStart(2, '0') + ':' + String(updateAt % 60).padStart(2, '0')"></span>
        </div>
        <v-slider v-model="updateAt" color="purple-lighten-2" track-color="grey" min="0" max="1425" :step="15">
        </v-slider>

        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-library</v-icon>
          Songs Count
          <span class="bold-picked ml-2" style="font-size: 1.7rem" v-text="songsCount"></span>
        </div>
        <v-slider v-model="songsCount" step="5" min="5" max="100" color="purple-lighten-2">
        </v-slider>
      </v-card-text>

      <!-- feature playlist -->
      <div v-if="featureEnabled" class="mx-auto pb-3">
        <v-card class="d-flex justify-space-between flex-wrap" style="justify-content: center !important;">
          <div>

            <v-card-title class="text-h5">
              Daily Smash
            </v-card-title>

            <v-card-subtitle>🕺 updates daily 🕺</v-card-subtitle>

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
          <span>{{ featureEnabled ? 'Disable' : 'Enable' }} Daily Smash</span>
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
      this.playlistImage = js.image;

      // form
      this.updateAt = js.update_at;
      this.songsCount = js.songs_count;
    }
  },

  props: ['feature', 'enabledFeatures'],

  data() {
    return {
      // config
      featureKey: 'daily-smash',

      // form
      updateAt: 7 * 60,
      songsCount: 50,

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

      const js = await this.api.toggleDailySmash({
        enabled: !this.featureEnabled,
        update_at: this.updateAt,
        songs_count: this.songsCount,
        timezone_offset: new Date().getTimezoneOffset()
      });

      this.$emit("feature-toggle", 'daily-smash', !this.featureEnabled)
      this.$emit("stop-loading");

      if (js.error) {
        this.$emit("display-error", js.error);
        return
      }

      this.featureEnabled = !this.featureEnabled;
      this.playlistId = js.playlist;
      this.playlistImage = js.image;
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