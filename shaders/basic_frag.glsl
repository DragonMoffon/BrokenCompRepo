#version 330

uniform sampler2D biomes;

in vec2 biomeUV;

out vec4 fragColor;

void main()
{
    fragColor = texture(biomes, biomeUV);
}