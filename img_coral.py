"""Simulate and draw random corals"""

from PIL import Image, ImageColor
from random import choice, random, randrange

def get_random_hue():
	"""get_random_hue() -> random non-blue hue"""
	return randrange(-60, 200) % 360

class CoralCell:
	"""CoralCell(hue, brightness) -> filled cell"""
	def __init__(self, hue, brightness):
		self.hue = hue
		self.brightness = brightness
	
	def get_child(self, hue_diff, p_brighter):
		"""cell.get_child()
			-> new coral cell with hue and brightness randomly mutated from parent"""
		new_hue = (self.hue + randrange(-hue_diff, hue_diff + 1)) % 360
		if self.brightness < 100 and random() < p_brighter:
			new_brightness = self.brightness + 1
		else:
			new_brightness = self.brightness
		return CoralCell(new_hue, new_brightness)

class Board:
	"""Board(nb_rows, nb_cols,
		hue_diff = 2, p_brightness = 0.8,
		down_bias = 0.3, right_bias = 0
	) -> 2D cell board
		nb_rows, nb_cols (int > 0): board dimensions
		hue_diff (int): max hue variation at each step
		p_brightness (float): average brightness increase with each step from a coral root
		down_bias (float 0 to 1): downward bias of drifting cells
			(larger is faster and produces denser corals)
		right_bias (float -1 to 1): rightward bias of drifting cells
			(negative for leftward bias)"""
	def __init__(self, nb_rows, nb_cols,
		hue_diff = 2, p_brightness = 0.8, down_bias = 0.3, right_bias = 0):
		self.nb_rows = nb_rows
		self.nb_cols = nb_cols
		
		self.cells = [
			[ None ] * nb_cols
			for _ in range(nb_rows)
		]
		
		self.step_nb = 0
		self.done = False
		
		nb_drifters = nb_cols # small impact on outcome, chosen for performance
		self.drifters = [ self.make_drifter() for _ in range(nb_drifters) ]
		
		self.hue_diff = hue_diff
		self.p_brightness = p_brightness * 100 / self.nb_rows
		self.p_down = 0.25 + 0.75 * down_bias
		self.p_right = 0.5 + right_bias / 2
	
	def get_coral_neighbour(self, row, col):
		"""b.get_coral_neighbour(row, col) ->
			random orthogonally adjacent CoralCell, or None if all are empty"""
		neighbours = []
		if row > 0:
			cell = self.cells[row-1][col]
			if cell:
				neighbours.append(cell)
		
		if row < self.nb_rows - 1:
			cell = self.cells[row+1][col]
			if cell:
				neighbours.append(cell)
		
		cell = self.cells[row][(col-1) % self.nb_cols]
		if cell:
			neighbours.append(cell)
		
		cell = self.cells[row][(col+1) % self.nb_cols]
		if cell:
			neighbours.append(cell)
		
		if neighbours:
			return choice(neighbours)
		return None
	
	def drift(self, row, col):
		"""b.drift(row, col) ->
			downwards-biased random orthogonally adjacent cell coords"""
		if row < self.nb_rows - 1 and random() < self.p_down:
			return (row + 1, col)
		
		# probability of drifting upwards vs horizontally is constant
		if row > 0 and random() < 0.333:
			return (row - 1, col)
		
		if random() < self.p_right:
			return (row, (col + 1) % self.nb_cols)
		else:
			return (row, (col - 1) % self.nb_cols)
	
	def make_drifter(self):
		"""b.make_drifter() -> coords of new drifting cell, random on top row"""
		return (0, randrange(self.nb_cols))
	
	def drifter_step(self, row, col):
		"""b.drifter_step(row, col) ->
			simulate evolution of drifting cell at (row, col)
			return new drifting cell position"""
		neighbour = self.get_coral_neighbour(row, col)
		if neighbour is not None:
			self.cells[row][col] = neighbour.get_child(self.hue_diff, self.p_brightness)
			if row == 0:
				self.done = True
			return self.make_drifter()
		elif row == self.nb_rows - 1:
			self.cells[row][col] = CoralCell(get_random_hue(), 0)
			return self.make_drifter()
		else:
			return self.drift(row, col)
	
	def step(self):
		"""b.step() -> simulate coral growth for 1 step"""
		self.step_nb += 1
		self.drifters = [ self.drifter_step(row, col) for (row, col) in self.drifters ]
	
	def run(self, print_step = 0, image_step = 0, save_prefix = None):
		"""b.run(print_step = 0, image_step = 0, save_prefix = None) ->
			simulate coral growth until complete
			print step number every print_step steps (0 for never)
			render intermediate image every image_step steps (0 for never)
			save intermediate images with prefix save_prefix (None to show without saving)"""
		self.step_nb = 0
		while not self.done:
			self.step()
			if print_step and self.step_nb % print_step == 0:
				print('Step', self.step_nb)
			if image_step and self.step_nb % image_step == 0:
				snapshot = self.print_to_image(show_drifters = True)
				if save_prefix is None:
					snapshot.show()
				else:
					snapshot.save('%s%d.png' % (save_prefix, self.step_nb // image_step))
		return self
	
	def __str__(self):
		return '\n'.join(
			''.join(
					self.print_cell(row, col)
					for col in range(self.nb_cols)
				)
			for row in range(self.nb_rows)
		)
	
	def print_cell(self, row, col):
		"""b.print_cell(row, col) -> text repr of cell"""
		if (row, col) in self.drifters:
			return '.'
		if self.cells[row][col]:
			return '#'
		return ' '
	
	def print_to_image(self, show_drifters = False):
		"""b.print_to_image(show_drifters = False) -> Pillow image representing board
			show_drifters: show drifting cells (in white)"""
		im = Image.new('RGB', (self.nb_cols, self.nb_rows), '#000088')
		px = im.load()
		for row in range(self.nb_rows):
			for col in range(self.nb_cols):
				cell = self.cells[row][col]
				if cell:
					colour = 'hsv(%d, 100%%, %d%%)' % (cell.hue, cell.brightness)
					px[col, row] = ImageColor.getrgb(colour)
		if show_drifters:
			for (row, col) in self.drifters:
				px[col, row] = (255, 255, 255)
		return im

def main(fname):
	board = Board(
		nb_rows = 500, nb_cols = 1200,
		hue_diff = 1,
		p_brightness = 1,
		down_bias = 0.15,
		right_bias = -.05
	)
	board.run(print_step = 1000, image_step = 30000)
	im = board.print_to_image()
	im.save(fname)
	im.show()

# Examples

EXAMPLES_DIR = 'examples'

SMALL_EXAMPLES = {
	'bright': { 'p_brightness': 100 },
	'dark': { 'p_brightness': 0.1 },
	'uniform': { 'hue_diff': 0 },
	'crazy_colours': { 'hue_diff': 15 },
	'sparse': { 'down_bias': 0 },
	'dense': { 'down_bias': 1 },
	'left': { 'right_bias': -1 },
	'right': { 'right_bias': 1 }
}

LARGE_EXAMPLES = {
	'coral': {},
	'seaweed': {
		'hue_diff': 1, 'p_brightness': 1,
		'down_bias': 0.1, 'right_bias': -0.05
	}
}

def generate_option_examples():
	from os import path
	
	def generate_example(name, nb_rows, nb_cols, options):
		fpath = path.join(EXAMPLES_DIR, name + '.png')
		print(fpath)
		Board(nb_rows, nb_cols, **options).run().print_to_image().save(fpath)
	
	for (name, options) in SMALL_EXAMPLES.items():
		generate_example(name, 250, 600, options)
	for (name, options) in LARGE_EXAMPLES.items():
		generate_example(name, 500, 1200, options)

def generate_print_examples():
	from os import path
	
	without_drifters_fpath = path.join(EXAMPLES_DIR, 'without_drifters.png')
	with_drifters_fpath = path.join(EXAMPLES_DIR, 'with_drifters.png')
	print(without_drifters_fpath)
	print(with_drifters_fpath)
	
	board = Board(200, 400)
	for _ in range(20000):
		board.step()
	board.print_to_image().save(without_drifters_fpath)
	board.print_to_image(show_drifters = True).save(with_drifters_fpath)

def generate_animation_example():
	from os import path, mkdir
	from errno import EEXIST
	
	frames_dir = path.join(EXAMPLES_DIR, 'frames')
	print(frames_dir)
	
	try:
		mkdir(frames_dir)
	except OSError as ex:
		if ex.errno != EEXIST:
			raise
	
	board = Board(200, 800)
	while not board.done:
		board.step()
		frame = board.print_to_image(show_drifters = True)
		fname = 'frame-{:0>10}.png'.format(board.step_nb)
		fpath = path.join(frames_dir, fname)
		frame.save(fpath)

def generate_all_examples():
	generate_option_examples()
	generate_print_examples()
	generate_animation_example()

if __name__ == '__main__':
	from sys import argv
	fname = argv[1] if len(argv) > 1 else 'coral.png'
	main(fname)
