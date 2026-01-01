from moviepy.video.io.VideoFileClip import VideoFileClip

clip = VideoFileClip("atm.mp4")
clip = clip.resized((300, 300)).subclipped(0, 2)
clip.write_gif("atm_cash_dispense.gif", fps=12)