all: 00000000.ivf 00000001.ivf 00000002.ivf 00000003.ivf 00000004.ivf

clean:
	rm -rf *.ivf *.state

### batch 0: [0, 4] ###

# stage 1: vpxenc

## 00000000

00000000-vpxenc.ivf: 00000000.y4m
	vpxenc --ivf --codec=vp8 --good --cpu-used=0 --end-usage=cq --min-q=0 --max-q=63 --cq-level=22 --buf-initial-sz=10000 --buf-optimal-sz=20000 --buf-sz=40000 --undershoot-pct=100 --passes=2 --auto-alt-ref=1 --threads=1 --token-parts=0 --tune=ssim --target-bitrate=4294967295 -o 00000000-vpxenc.ivf 00000000.y4m

00000000.ivf: 00000000-vpxenc.ivf
	xc-terminate-chunk 00000000-vpxenc.ivf 00000000.ivf

00000000-0.state: 00000000.ivf
	xc-dump 00000000.ivf 00000000-0.state

## 00000001

00000001-vpxenc.ivf: 00000001.y4m
	vpxenc --ivf --codec=vp8 --good --cpu-used=0 --end-usage=cq --min-q=0 --max-q=63 --cq-level=22 --buf-initial-sz=10000 --buf-optimal-sz=20000 --buf-sz=40000 --undershoot-pct=100 --passes=2 --auto-alt-ref=1 --threads=1 --token-parts=0 --tune=ssim --target-bitrate=4294967295 -o 00000001-vpxenc.ivf 00000001.y4m

00000001-0.ivf: 00000001-vpxenc.ivf
	xc-terminate-chunk 00000001-vpxenc.ivf 00000001-0.ivf

00000001-0.state: 00000001-0.ivf
	xc-dump 00000001-0.ivf 00000001-0.state

## 00000002

00000002-vpxenc.ivf: 00000002.y4m
	vpxenc --ivf --codec=vp8 --good --cpu-used=0 --end-usage=cq --min-q=0 --max-q=63 --cq-level=22 --buf-initial-sz=10000 --buf-optimal-sz=20000 --buf-sz=40000 --undershoot-pct=100 --passes=2 --auto-alt-ref=1 --threads=1 --token-parts=0 --tune=ssim --target-bitrate=4294967295 -o 00000002-vpxenc.ivf 00000002.y4m

00000002-0.ivf: 00000002-vpxenc.ivf
	xc-terminate-chunk 00000002-vpxenc.ivf 00000002-0.ivf

00000002-0.state: 00000002-0.ivf
	xc-dump 00000002-0.ivf 00000002-0.state

## 00000003

00000003-vpxenc.ivf: 00000003.y4m
	vpxenc --ivf --codec=vp8 --good --cpu-used=0 --end-usage=cq --min-q=0 --max-q=63 --cq-level=22 --buf-initial-sz=10000 --buf-optimal-sz=20000 --buf-sz=40000 --undershoot-pct=100 --passes=2 --auto-alt-ref=1 --threads=1 --token-parts=0 --tune=ssim --target-bitrate=4294967295 -o 00000003-vpxenc.ivf 00000003.y4m

00000003-0.ivf: 00000003-vpxenc.ivf
	xc-terminate-chunk 00000003-vpxenc.ivf 00000003-0.ivf

00000003-0.state: 00000003-0.ivf
	xc-dump 00000003-0.ivf 00000003-0.state

## 00000004

00000004-vpxenc.ivf: 00000004.y4m
	vpxenc --ivf --codec=vp8 --good --cpu-used=0 --end-usage=cq --min-q=0 --max-q=63 --cq-level=22 --buf-initial-sz=10000 --buf-optimal-sz=20000 --buf-sz=40000 --undershoot-pct=100 --passes=2 --auto-alt-ref=1 --threads=1 --token-parts=0 --tune=ssim --target-bitrate=4294967295 -o 00000004-vpxenc.ivf 00000004.y4m

00000004-0.ivf: 00000004-vpxenc.ivf
	xc-terminate-chunk 00000004-vpxenc.ivf 00000004-0.ivf

00000004-0.state: 00000004-0.ivf
	xc-dump 00000004-0.ivf 00000004-0.state

# stage 2: reencode-first-frame

## 00000001

00000001-1.state 00000001.ivf: 00000001.y4m 00000001-0.ivf 00000000-0.state
	xc-enc -W -w 0.75 -i y4m -o 00000001.ivf -r -I 00000000-0.state -p 00000001-0.ivf -O 00000001-1.state 00000001.y4m
## 00000002

00000002-1.ivf: 00000002.y4m 00000002-0.ivf 00000001-0.state
	xc-enc -W -w 0.75 -i y4m -o 00000002-1.ivf -r -I 00000001-0.state -p 00000002-0.ivf  00000002.y4m
## 00000003

00000003-1.ivf: 00000003.y4m 00000003-0.ivf 00000002-0.state
	xc-enc -W -w 0.75 -i y4m -o 00000003-1.ivf -r -I 00000002-0.state -p 00000003-0.ivf  00000003.y4m
## 00000004

00000004-1.ivf: 00000004.y4m 00000004-0.ivf 00000003-0.state
	xc-enc -W -w 0.75 -i y4m -o 00000004-1.ivf -r -I 00000003-0.state -p 00000004-0.ivf  00000004.y4m
# stage 3: rebase

## 00000002

00000002-1.state 00000002.ivf: 00000002.y4m 00000002-1.ivf 00000001-0.state 00000001-1.state
	xc-enc -W -w 0.75 -i y4m -o 00000002.ivf -r -I 00000001-1.state -p 00000002-1.ivf -S 00000001-0.state -O 00000002-1.state 00000002.y4m
## 00000003

00000003-1.state 00000003.ivf: 00000003.y4m 00000003-1.ivf 00000002-0.state 00000002-1.state
	xc-enc -W -w 0.75 -i y4m -o 00000003.ivf -r -I 00000002-1.state -p 00000003-1.ivf -S 00000002-0.state -O 00000003-1.state 00000003.y4m
## 00000004

00000004.ivf: 00000004.y4m 00000004-1.ivf 00000003-0.state 00000003-1.state
	xc-enc -W -w 0.75 -i y4m -o 00000004.ivf -r -I 00000003-1.state -p 00000004-1.ivf -S 00000003-0.state  00000004.y4m
