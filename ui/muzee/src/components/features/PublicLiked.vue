<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'"
    color="purple-lighten-4">
    <span v-if="state === 'idle'">

      <!-- form -->
      <!-- no form -->

      <!-- feature playlist -->
      <div v-if="featureEnabled" class="mx-auto pb-3">

        <PlaylistCard v-if="playlistId" :playlistId="playlistId" />

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
import PlaylistCard from '@/components/PlaylistCard.vue';


export default {
  components: {
    PlaylistCard
  },
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
      });

      this.$emit("feature-toggle", this.featureKey, !this.featureEnabled)
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
