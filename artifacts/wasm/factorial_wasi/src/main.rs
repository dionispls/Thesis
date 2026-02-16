use std::time::Instant;

fn factorial(n: u32) -> u128 {
    let mut res: u128 = 1;
    for i in 2..=n {
        res *= i as u128;
    }
    res
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let n: u32 = match args[1].parse() {
        Ok(v) => v,
        Err(_) => {
            std::process::exit(2);
        }
    };

    let t0 = Instant::now();
    let result = factorial(n);
    let exec_ns = t0.elapsed().as_nanos();

    println!(
        r#"{{"backend":"wasm","n":{},"result":"{}","exec_ns":{}}}"#,
        n, result, exec_ns
    );
}