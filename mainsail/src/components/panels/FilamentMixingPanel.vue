<template>
    <panel
        v-if="showPanel"
        :title="$t('Panels.FilamentMixingPanel.Headline')"
        :icon="mdiPalette"
        :collapsible="true"
        card-class="filament-mixing-panel">
        <v-card-text>
            <v-alert v-if="!registered" dense text type="warning" class="mb-3">
                {{ $t('Panels.FilamentMixingPanel.NotRegisteredWarning') }}
            </v-alert>

            <div class="d-flex align-center justify-space-between mb-3">
                <span class="text--secondary">{{ $t('Panels.FilamentMixingPanel.Status') }}</span>
                <v-chip small :color="registered ? 'success' : 'warning'" text-color="white">
                    {{
                        registered
                            ? $t('Panels.FilamentMixingPanel.Registered')
                            : $t('Panels.FilamentMixingPanel.NotRegistered')
                    }}
                </v-chip>
            </div>

            <v-simple-table dense>
                <thead>
                    <tr>
                        <th>{{ $t('Panels.FilamentMixingPanel.Channel') }}</th>
                        <th>{{ $t('Panels.FilamentMixingPanel.Axis') }}</th>
                        <th class="text-right">{{ $t('Panels.FilamentMixingPanel.Position') }}</th>
                        <th>{{ $t('Panels.FilamentMixingPanel.KlipperObject') }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="channel in channels" :key="channel.axis">
                        <td>
                            <span class="_channel-dot mr-2" :style="{ backgroundColor: channel.color }" />
                            {{ channel.name }}
                        </td>
                        <td>{{ channel.axis }}</td>
                        <td class="text-right">{{ channelPosition(channel.axis) }}</td>
                        <td>{{ axisObjectName(channel.axis) }}</td>
                    </tr>
                </tbody>
            </v-simple-table>

            <v-btn
                small
                color="primary"
                class="mt-4"
                :disabled="printerIsPrinting"
                @click="registerAxes">
                {{ $t('Panels.FilamentMixingPanel.RegisterAxes') }}
            </v-btn>
        </v-card-text>
    </panel>
</template>

<script lang="ts">
import { Component, Mixins } from 'vue-property-decorator'
import BaseMixin from '@/components/mixins/base'
import Panel from '@/components/ui/Panel.vue'
import { mdiPalette } from '@mdi/js'

type AxisMap = Record<string, number>
type ExtraAxes = Record<string, number>

const CHANNELS = [
    { name: 'Cyan', axis: 'A', color: '#00bcd4' },
    { name: 'Magenta', axis: 'B', color: '#e91e63' },
    { name: 'Yellow', axis: 'C', color: '#fdd835' },
    { name: 'Black', axis: 'D', color: '#424242' },
    { name: 'White', axis: 'H', color: '#eeeeee' },
]

@Component({
    components: {
        Panel,
    },
})
export default class FilamentMixingPanel extends Mixins(BaseMixin) {
    mdiPalette = mdiPalette
    channels = CHANNELS

    get axisMap(): AxisMap {
        return this.$store.state.printer.gcode_move?.axis_map ?? {}
    }

    get extraAxes(): ExtraAxes {
        return this.$store.state.printer.toolhead?.extra_axes ?? {}
    }

    get gcodePosition(): number[] {
        return this.$store.state.printer.gcode_move?.gcode_position ?? []
    }

    get hasRegisterMacro(): boolean {
        return 'REGISTER_CMYKW_AXES' in (this.$store.state.printer.gcode?.commands ?? {})
    }

    get hasAnyChannelAxis(): boolean {
        return this.channels.some((channel) => channel.axis in this.axisMap)
    }

    get registered(): boolean {
        return this.channels.every((channel) => channel.axis in this.axisMap)
    }

    get showPanel(): boolean {
        return this.klipperReadyForGui && (this.hasRegisterMacro || this.hasAnyChannelAxis)
    }

    channelPosition(axis: string): string {
        const index = this.axisMap[axis]
        if (index === undefined) return '--'

        const position = this.gcodePosition[index]
        return typeof position === 'number' ? `${position.toFixed(3)} mm` : '--'
    }

    axisObjectName(axis: string): string {
        const index = this.axisMap[axis]
        if (index === undefined) return '--'

        const entry = Object.entries(this.extraAxes).find(([, axisIndex]) => axisIndex === index)
        return entry ? entry[0].replace('manual_stepper ', '') : '--'
    }

    registerAxes(): void {
        const gcode = 'REGISTER_CMYKW_AXES'

        this.$store.dispatch('server/addEvent', { message: gcode, type: 'command' })
        this.$socket.emit('printer.gcode.script', { script: gcode }, { loading: 'registerCmykwAxes' })
    }
}
</script>

<style scoped>
._channel-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 50%;
}
</style>
