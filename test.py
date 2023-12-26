import turtle

tt = turtle.Turtle()

radius = 50
#Loop to draw a spiral circle
for i in range(100):
    tt.circle(radius + i, 45)

# Finish by turtle.done() command
turtle.done()