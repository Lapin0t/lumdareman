#![feature(const_fn)]
extern crate sdl2;
extern crate sdl2_sys;

use std::path::Path;
use std::io::{self,Read};
use std::fs::File;
use std::time::{Instant,Duration};
use std::ops::Mul;


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

    fn get(&self, x: i32, y: i32) -> &TILE {
        return &self.tiles[x as usize + self.width * y as usize];
    }
}

struct Ticker {
    start: Instant,  // ticking start time
    end: Instant,    // ticking end time
}

impl Ticker {
    fn new() -> Ticker {
        Ticker { start: Instant::now(), end: Instant::now() }
    }
    fn tick(&mut self, min_d: Duration) -> f32 {
        let start = Instant::now();
        let work_d = start.duration_since(self.end);
        let frame_d = start.duration_since(self.start);

        println!("work: {:.4}ms, frame: {:.4}ms",
                 work_d.as_secs_f32() * 1000.,
                 frame_d.as_secs_f32() * 1000.);

        if frame_d < min_d {
            std::thread::sleep(min_d - frame_d);
        }

        let end = Instant::now();
        let true_d = end.duration_since(self.end);
        self.start = start;
        self.end = end;
        return true_d.as_secs_f32();
    }
}

#[derive(PartialEq,Eq,Copy,Clone)]
enum Sign { Pos, Zer, Neg }

impl Into<f32> for Sign {
    #[inline]
    fn into(self) -> f32 {
        match self {
            Sign::Pos => 1.,
            Sign::Zer => 0.,
            Sign::Neg => -1.,
        }
    }
}

impl Into<i32> for Sign {
    #[inline]
    fn into(self) -> i32 {
        match self {
            Sign::Pos => 1,
            Sign::Zer => 0,
            Sign::Neg => -1,
        }
    }
}

impl From<f32> for Sign {
    #[inline]
    fn from(x: f32) -> Sign {
        if x == 0. { Sign::Zer }
        else if x > 0. { Sign::Pos }
        else { Sign::Neg }
    }
}

impl From<bool> for Sign {
    #[inline]
    fn from(x: bool) -> Sign {
        if x { Sign::Pos } else { Sign::Neg }
    }
}


impl Mul<Sign> for Sign {
    type Output = Sign;

    #[inline]
    fn mul(self, rhs: Sign) -> Sign {
        match (self, rhs) {
            (Sign::Zer, _) | (_, Sign::Zer) => { Sign::Zer },
            (Sign::Pos, Sign::Neg) | (Sign::Neg, Sign::Pos) => { Sign::Neg },
            (Sign::Pos, Sign::Pos) | (Sign::Neg, Sign::Neg) => { Sign::Pos },
        }
    }
}

impl Mul<i32> for Sign {
    type Output = i32;

    #[inline]
    fn mul(self, rhs: i32) -> i32 {
        match self {
            Sign::Pos => rhs,
            Sign::Zer => 0,
            Sign::Neg => -rhs,
        }
    }
}


impl Mul<f32> for Sign {
    type Output = f32;

    #[inline]
    fn mul(self, rhs: f32) -> f32 {
        match self {
            Sign::Pos => rhs,
            Sign::Zer => 0.,
            Sign::Neg => -rhs,
        }
    }
}

fn main() {
    let sdl_ctx = sdl2::init().unwrap();
    let _image_ctx = image::init(image::InitFlag::PNG).unwrap();
    let video_ctx = sdl_ctx.video().unwrap();

    let FRAME_T: Duration = Duration::from_secs_f32(1. / 30.);

    let window = video_ctx.window("demo", 800, 600).build().unwrap();
    let mut canvas = window.into_canvas().present_vsync().build().unwrap();
    canvas.set_draw_color(Color::RGB(0, 255, 255));

    let tex_creator = canvas.texture_creator();
    let TEX_TILES = tex_creator.load_texture("assets/sb1_blocks.png").unwrap();
    let TEX_CHAR = tex_creator.load_texture("assets/sb1_items.png").unwrap();

    const TILE_SCALE: i32 = TILE::SIZE * 2;
    const TILE_SCALEf: f32 = TILE_SCALE as f32;
    const SPEED: f32 = 4. * TILE_SCALEf;
    const SNAP: f32 = TILE_SCALEf / 4.;

    let CHAR_SRC = Rect::new(16, 0, 16, 16);




    //let map = Map::from_file("assets/empty.map").unwrap();
    let map = Map::basic(10, 10);

    let mut event_pump = sdl_ctx.event_pump().unwrap();

    let mut tile_dst = Rect::new(0, 0, TILE_SCALE as u32, TILE_SCALE as u32);

    let mut player_dst = Rect::new(0, 0, TILE_SCALE as u32, TILE_SCALE as u32);
    let mut ppos_i: (i32, i32) = (1, 1);
    let mut ppos_f: (f32, f32) = (0., 0.);
    let mut pinput: (bool, bool) = (false, false);
    let mut pori: (Sign, Sign) = (Sign::Pos, Sign::Pos);

    let mut ticker = Ticker::new();

    'running: loop {
        let delta_t = ticker.tick(FRAME_T);

        for event in event_pump.poll_iter() {
            match event {
                Event::Quit {..} => { break 'running; },
                Event::KeyDown { keycode: Some(Keycode::Escape), .. } => {
                    break 'running;
                }
                Event::KeyDown { keycode: Some(Keycode::D), .. } => {
                    pinput.0 = true;
                    pori.0 = Sign::Pos;
                }
                Event::KeyDown { keycode: Some(Keycode::S), .. } => {
                    pinput.1 = true;
                    pori.1 = Sign::Pos;
                }
                Event::KeyDown { keycode: Some(Keycode::A), .. } => {
                    pinput.0 = true;
                    pori.0 = Sign::Neg;
                }
                Event::KeyDown { keycode: Some(Keycode::W), .. } => {
                    pinput.1 = true;
                    pori.1 = Sign::Neg;
                }
                Event::KeyUp { keycode: Some(Keycode::D), .. } => {
                    if (pori.0 == Sign::Pos) { pinput.0 = false; }
                }
                Event::KeyUp { keycode: Some(Keycode::S), .. } => {
                    if (pori.1 == Sign::Pos) { pinput.1 = false; }
                }
                Event::KeyUp { keycode: Some(Keycode::A), .. } => {
                    if (pori.0 == Sign::Neg) { pinput.0 = false; }
                }
                Event::KeyUp { keycode: Some(Keycode::W), .. } => {
                    if (pori.1 == Sign::Neg) { pinput.1 = false; }
                }
                _ => {}
            }
        }

        if pinput.0 { ppos_f.0 += pori.0 * SPEED * delta_t; }
        if pinput.1 { ppos_f.1 += pori.1 * SPEED * delta_t; }

        if pori.0 * ppos_f.0 > TILE_SCALEf / 2. {
            ppos_f.0 -= pori.0 * TILE_SCALEf;
            ppos_i.0 += Into::<i32>::into(pori.0);
        };
        if pori.1 * ppos_f.1 > TILE_SCALEf / 2. {
            ppos_f.1 -= pori.1 * TILE_SCALEf;
            ppos_i.1 += Into::<i32>::into(pori.1);
        };

        // quadrant of center
        let q0 = Sign::from(ppos_f.0);
        let q1 = Sign::from(ppos_f.1);

        let c10 = q0 != Sign::Zer &&                    map.get(ppos_i.0 + Into::<i32>::into(q0), ppos_i.1                        ).is_solid();
        let c01 = q1 !=                    Sign::Zer && map.get(ppos_i.0,                         ppos_i.1 + Into::<i32>::into(q1)).is_solid();
        let c11 = q0 != Sign::Zer && q1 != Sign::Zer && map.get(ppos_i.0 + Into::<i32>::into(q0), ppos_i.1 + Into::<i32>::into(q1)).is_solid();

        if q0 * ppos_f.0 + q1 * ppos_f.1 > 0.5 * TILE_SCALEf && c11 {
            let a = Sign::from(q0 * ppos_f.0 - q1 * ppos_f.1);
            let f0 = ppos_f.0;
            let f1 = ppos_f.1;
            /*if f32::abs(f0 - f1) < 1. {
                ppos_f.0 = q0 * 0.5 * TILE_SCALEf;
                ppos_f.1 = q1 * 0.5 * TILE_SCALEf;
            } else if q0 * f0 < q1 * f1 {
                ppos_f.0 = q0 * (0.5 * TILE_SCALEf - q1 * ppos_f.1);
            } else {
                ppos_f.1 = q1 * (0.5 * TILE_SCALEf - q0 * ppos_f.0);
            }*/
            ppos_f.0 = (f0 + q0*(0.5*TILE_SCALEf - q1*f1)) * 0.5;
            ppos_f.1 = (f1 + q1*(0.5*TILE_SCALEf - q0*f0)) * 0.5;
        }
        if c10 { ppos_f.0 = 0.; }
        if c01 { ppos_f.1 = 0.; }

        player_dst.x = (TILE_SCALE * ppos_i.0) + (ppos_f.0 as i32);
        player_dst.y = (TILE_SCALE * ppos_i.1) + (ppos_f.1 as i32);


        ////////////
        // rendering
        canvas.clear();

        for y in 0..map.height {
            for x in 0..map.width {
                tile_dst.set_x(TILE_SCALE * x as i32);
                tile_dst.set_y(TILE_SCALE * y as i32);
                canvas.copy(&TEX_TILES,
                            map.tiles[x + map.width * y].src_rect(),
                            tile_dst).unwrap();
            }
        }

        canvas.copy(&TEX_CHAR, CHAR_SRC, player_dst).unwrap();

        canvas.present();
    }
}
