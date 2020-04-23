extern crate sdl2;
extern crate sdl2_sys;

use std::path::Path;
use std::io::{self,Read};
use std::fs::File;
use std::time::{Instant,Duration};

use sdl2_sys::SDL_Rect;
use sdl2::VideoSubsystem;
use sdl2::image::{self,LoadTexture};
use sdl2::render::{WindowCanvas,Texture,TextureCreator};
use sdl2::keyboard::Keycode;
use sdl2::event::Event;
use sdl2::rect::Rect;
use sdl2::pixels::Color;
use sdl2::video::WindowContext;


#[derive(Copy,Clone)]
enum TILE {
    BRICK,
    WALL,
    EMPTY,
}

impl TILE {
    const SIZE: i32 = 16;
    const SRC: [SDL_Rect; 3] = [
        SDL_Rect { x: 2*TILE::SIZE, y: 0, w: TILE::SIZE, h: TILE::SIZE },
        SDL_Rect { x: 3*TILE::SIZE, y: 0, w: TILE::SIZE, h: TILE::SIZE },
        SDL_Rect { x: 4*TILE::SIZE, y: 0, w: TILE::SIZE, h: TILE::SIZE },
    ];

    const FILE: &'static str = "assets/sb1_blocks.png";

    #[inline]
    fn src_rect(&self) -> Rect {
        unsafe { std::mem::transmute(TILE::SRC[*self as usize]) }
    }

    fn is_solid(&self) -> bool {
        match *self {
            TILE::BRICK => true,
            TILE::WALL => true,
            TILE::EMPTY => false,
        }
    }
}


const SHEETS_NUM: usize = 1;
static SHEETS_FILE: [&'static str; SHEETS_NUM] = [
    "assets/sb1_blocks.png"
];


struct Sprite {
    sheet: usize,
    src: Rect,
    dst: Rect,
}

struct DrawCtx {
    canvas: WindowCanvas,
    sheets: [Texture; SHEETS_NUM],
}

impl DrawCtx where {
    fn new(video_ctx: &VideoSubsystem) -> DrawCtx {
        let window = video_ctx.window("demo", 800, 600).build().unwrap();
        let mut canvas = window.into_canvas().present_vsync().build().unwrap();
        canvas.set_draw_color(Color::RGB(0, 255, 255));

        let creator = canvas.texture_creator();
        let blocs = creator.load_texture("assets/sb1_blocks.png").unwrap();
        let sheets = [blocs];

        return DrawCtx { canvas, sheets }
    }

    fn draw(&mut self, s: &Sprite) -> Result<(), String> {
        self.canvas.copy(&self.sheets[s.sheet], s.src, s.dst)
    }
}


struct Map {
    width: usize,
    height: usize,
    tiles: Vec<TILE>,
}

impl Map {
    /*fn from_file<P: AsRef<Path>>(path: P) -> io::Result<Map> {
        let mut f = File::open(path)?;

        let mut size_buf = [0u8; 2];
        let n = f.read(&mut size_buf)?;
        if n < 2 {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "bad map"));
        }
        let width = size_buf[0] as usize;
        let height = size_buf[1] as usize;

        let mut tiles = vec![0; width * height];
        f.read_exact(&mut tiles)?;

        return Ok(Map { width, height, tiles });
    }*/

    fn basic(m: usize, n: usize) -> Map {
        let width = 3 + 2*m;
        let height = 3 + 2*n;
        let mut tiles = vec![TILE::EMPTY; width * height];

        // borders
        for i in 0..width {
            tiles[i] = TILE::WALL;
            tiles[i + (height - 1) * width] = TILE::WALL;
        }
        for i in 0..height {
            tiles[i * width] = TILE::WALL;
            tiles[(i + 1) * width - 1] = TILE::WALL;
        }

        // battleground
        for y in 0..n {
            for x in 0..m {
                tiles[2 + 2*x + (2 + 2*y) * width] = TILE::WALL;
            }
        }
        return Map { width, height, tiles };
    }
}

fn main() {
    println!("Rect: {:?}, SDL_Rect: {:?}", std::mem::size_of::<Rect>(), std::mem::size_of::<sdl2_sys::SDL_Rect>());
    let sdl_ctx = sdl2::init().unwrap();
    let _image_ctx = image::init(image::InitFlag::PNG).unwrap();
    let video_ctx = sdl_ctx.video().unwrap();

    let FRAME_T: Duration = Duration::from_secs_f32(1. / 60.);

    let window = video_ctx.window("demo", 800, 600).build().unwrap();
    let mut canvas = window.into_canvas().present_vsync().build().unwrap();
    canvas.set_scale(2., 2.);
    canvas.set_draw_color(Color::RGB(0, 255, 255));

    let tex_creator = canvas.texture_creator();
    let TEX_TILES = tex_creator.load_texture("assets/sb1_blocks.png").unwrap();
    let TEX_CHAR = tex_creator.load_texture("assets/sb1_items.png").unwrap();
    let CHAR_SRC = Rect::new(16, 0, 16, 16);

    let SPEED = 3. * (TILE::SIZE as f32);
    let SNAP = TILE::SIZE / 8;



    //let map = Map::from_file("assets/empty.map").unwrap();
    let map = Map::basic(10, 10);

    let mut event_pump = sdl_ctx.event_pump().unwrap();

    let mut tile_dst = Rect::new(0, 0, TILE::SIZE as u32, TILE::SIZE as u32);

    let mut player_dst = Rect::new(0, 0, TILE::SIZE as u32, TILE::SIZE as u32);
    let mut player_pos_i: (i32, i32) = (1, 1);
    let mut player_pos_f: (f32, f32) = (0., 0.);
    let mut player_in: (bool, bool) = (false, false);
    let mut player_d: (i32, i32) = (0, 0);
    let mut player_o: (i32, i32) = (0, 0);

    let mut t_prev = Instant::now();
    let mut t_start = Instant::now();
    let mut dur = Duration::from_secs(0);
    let mut delta_t: f32 = 0.;

    'running: loop {
        t_start = Instant::now();
        dur = t_start.duration_since(t_prev);
        if dur < FRAME_T { std::thread::sleep(FRAME_T - dur) }
        delta_t = t_start.duration_since(t_prev).as_secs_f32();
        println!("{:?}", delta_t * 1000.);
        t_prev = t_start;

        canvas.clear();

        for event in event_pump.poll_iter() {
            match event {
                Event::Quit {..} => { break 'running },
                Event::KeyDown { keycode: Some(Keycode::E), .. } => {
                    player_o.0 = 1;
                    player_in.0 = true;
                }
                Event::KeyDown { keycode: Some(Keycode::O), .. } => {
                    player_o.1 = 1;
                    player_in.1 = true;
                }
                Event::KeyDown { keycode: Some(Keycode::A), .. } => {
                    player_o.0 = -1;
                    player_in.0 = true;
                }
                Event::KeyDown { keycode: Some(Keycode::Comma), .. } => {
                    player_in.1 = true;
                    player_o.1 = -1;
                }
                Event::KeyUp { keycode: Some(Keycode::E), .. } => {
                    if (player_o.0 == 1) { player_in.0 = false; }
                }
                Event::KeyUp { keycode: Some(Keycode::O), .. } => {
                    if (player_o.1 == 1) { player_in.1 = false; }
                }
                Event::KeyUp { keycode: Some(Keycode::A), .. } => {
                    if (player_o.0 == -1) { player_in.0 = false; }
                }
                Event::KeyUp { keycode: Some(Keycode::Comma), .. } => {
                    if (player_o.1 == -1) { player_in.1 = false; }
                }
                _ => {}
            }
        }

        let g0 = player_pos_f.0 * (player_o.0 as f32);
        let g1 = player_pos_f.1 * (player_o.1 as f32);

        player_d = player_o;
        let d0 = if !player_in.0 && 0 <= g0 && g0 <  { -player_o.0 } else { player_o.0 };
        if !player_in.0 {
            if g0 <= 0. {
            }
        }

        /*let g0 = player_pos_f.0 * (player_d.0 as f32);
        let g1 = player_pos_f.1 * (player_d.1 as f32);
        match (g0 >= 0., g1 >= 0.) {
            (true,  true)  => {
                let c10 = map.tiles[]
            },
            (true,  false) => {
            },
            (false, true)  => {
            },
            (false, false) => {
            },
        }*/

        player_pos_f.0 += (player_d.0 as f32) * SPEED * delta_t;
        player_pos_f.1 += (player_d.1 as f32) * SPEED * delta_t;

        player_dst.x = (TILE::SIZE * player_pos_i.0) + (player_pos_f.0 as i32);
        player_dst.y = (TILE::SIZE * player_pos_i.1) + (player_pos_f.1 as i32);



        for y in 0..map.height {
            for x in 0..map.width {
                tile_dst.set_x(TILE::SIZE * x as i32);
                tile_dst.set_y(TILE::SIZE * y as i32);
                canvas.copy(&TEX_TILES,
                            map.tiles[x + map.width * y].src_rect(),
                            tile_dst).unwrap();
            }
        }

        canvas.copy(&TEX_CHAR, CHAR_SRC, player_dst).unwrap();

        canvas.present();
    }
}
