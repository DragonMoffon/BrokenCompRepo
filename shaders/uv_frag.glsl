#version 330

vec2 iResoultion = vec2(1920, 1080);

uniform float x_adjustment;
uniform sampler2D ichannel0;

in vec4 gl_FragCoord;
in vec2 v_uv;

vec2 mod_pos = mod(gl_FragCoord.xy + vec2(x_adjustment, 0.0), iResoultion);

out vec4 fragColor;

void main() {
    fragColor = texture(ichannel0, mod_pos/iResoultion);
}
