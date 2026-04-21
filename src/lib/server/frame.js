/**
 * Strip the `online` boolean from every device in a frame, so Newton has to
 * infer online/offline from the traffic evidence (flows, bytes, protocols).
 *
 * The UI still uses `online` for the ground-truth column — this only affects
 * what goes to the model.
 */
export function redactOnline(frame) {
	return {
		...frame,
		devices: frame.devices.map((d) => {
			// eslint-disable-next-line no-unused-vars
			const { online: _online, ...rest } = d;
			return rest;
		})
	};
}
