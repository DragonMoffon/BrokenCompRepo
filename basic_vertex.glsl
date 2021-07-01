#version 420

in vec2 inPos;
in vec3 inColor;

out vec4 color;

void main()
{
    color = vec4(inColor, 1);

    gl_Position = vec4(inPos, 0, 1);
}