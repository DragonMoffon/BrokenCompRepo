#version 330

in vec2 inPos;
in vec2 inBiomeUV;

out vec4 color;
out vec2 biomeUV;

void main()
{
    gl_Position = vec4(inPos, 0, 1);
    biomeUV = inBiomeUV;
}